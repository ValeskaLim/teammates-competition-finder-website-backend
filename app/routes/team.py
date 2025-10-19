from flask import Blueprint, jsonify, request, current_app
import os
import time
from werkzeug.utils import secure_filename
from datetime import datetime
from app.extensions import db
from app.models import Competition, ProofTransaction, TeamInvitation, TeamJoin, Teams, Users
from app.routes.generic import get_current_user_object, now_jakarta
from flask_mail import Message
import threading
from requests import post
from app.routes.generic import send_async_email
from app.utils.response import success_response, error_response

team_bp = Blueprint('team', __name__, url_prefix="/team")


@team_bp.route("/get-list-team-user-request", methods=["POST"])
def get_list_team_user_request():
    try:
        current_user = get_current_user_object()
        query = TeamJoin.query

        join_requests = query.filter(
            TeamJoin.user_id == current_user.user_id, TeamJoin.status == "P"
        ).all()

        results = []
        for request in join_requests:
            team = Teams.query.get(request.team_id)
            if team:
                leader = Users.query.get(team.leader_id)
                leader_name = leader.fullname if leader else "Unknown"
                results.append({
                    "team_id": team.team_id,
                    "team_name": team.team_name,
                    "leader_id": team.leader_id,
                    "leader_name": leader_name,
                    "status": request.status
                })

        return success_response("Join requests retrieved successfully", data=results, status=200)

    except Exception as e:
        return error_response(f"Error fetching join requests: {str(e)}", status=500)

@team_bp.route("/check-is-leader", methods=["POST"])
def check_is_leader():
    try:
        current_user = get_current_user_object()
        query = Teams.query

        is_leader = query.filter(
            Teams.leader_id == current_user.user_id, Teams.member_id.ilike(f"%{current_user.user_id}%")
        ).first()

        if is_leader is None:
            return success_response("User is not a team leader", data={"isLeader": False}, status=200)

        return success_response("User is a team leader", data={"isLeader": True}, status=200)

    except Exception as e:
        return error_response(f"Error fetching users: {str(e)}", status=500)
    
@team_bp.route("/check-any-competitions-joined", methods=["POST"])
def check_any_competitions_joined():
    try:
        current_user = get_current_user_object()
        current_user_id = str(current_user.user_id)
        query = Teams.query

        current_team = query.filter(
            Teams.member_id.ilike(f"%{current_user_id}%")
        ).first()

        if current_team is None or current_team.competition_id is None:
            return success_response("User's team has not joined any competition", data={"hasJoined": False}, status=200)

        return success_response("User's team has joined a competition", data={"hasJoined": True}, status=200)
    except Exception as e:
        return error_response(f"Error fetching users: {str(e)}", status=500)
    
@team_bp.route("/check-number-invitations", methods=["POST"])
def check_number_invitation():
    try:
        current_user = get_current_user_object()
        query = TeamInvitation.query

        invitation_count = query.filter(
            TeamInvitation.inviter_id == current_user.user_id, TeamInvitation.status == "P"
        ).count()

        return success_response("Invitation count fetched successfully", data={"count": invitation_count}, status=200)

    except Exception as e:
        return error_response(f"Error fetching invitation count: {str(e)}", status=500)

@team_bp.route("/create-team", methods=["POST"])
def create_team():
    try:
        req = request.get_json()
        query = Teams.query

        check_is_exist = query.filter(
            (Teams.team_name == req['team_name']) | (Teams.leader_id == req['leader_id'])
        ).first()

        if check_is_exist is not None:
            return error_response("Team / user already exist", status=406)

        new_team = Teams(
            member_id = str(req["leader_id"]),
            team_name = req["team_name"],
            is_finalized = False,
            competition_id = None,
            date_created = now_jakarta(),
            date_updated = now_jakarta(),
            leader_id = req["leader_id"],
        )

        db.session.add(new_team)
        db.session.commit()

        return success_response("Team successfully created", status=200)

    except Exception as e:
        return error_response(f"Error creating team: {str(e)}", status=500)
    
@team_bp.route("/edit-team", methods=["POST"])
def edit_team():
    try:
        req = request.get_json()
        query = Teams.query

        current_team = query.filter(
            Teams.team_id == req['team_id']
        ).first()

        if current_team is None:
            return error_response("Team not found", status=404)
        
        if len(req["description"]) > 500:
            return error_response("Description exceeds maximum length of 500 characters", status=400)
        
        if len(req["notes"]) > 500:
            return error_response("Notes exceeds maximum length of 500 characters", status=400)

        current_team.description = req["description"]
        current_team.notes = req["notes"]
        current_team.date_updated = now_jakarta()

        db.session.commit()

        return success_response("Team successfully updated", status=200)

    except Exception as e:
        return error_response(f"Error updating team: {str(e)}", status=500)
    
@team_bp.route("/finalize-team", methods=["POST"])
def finalize_team():
    try:
        team_id = request.form.get("team_id")
        if not team_id:
            return error_response("team_id required", status=400)

        team = Teams.query.filter(Teams.team_id == int(team_id)).first()
        if team is None:
            return error_response("Team not found", status=404)

        current_user = get_current_user_object()
        if current_user.user_id != team.leader_id:
            return error_response("Only the leader can finalize", status=406)

        # Handle proof image
        proof_file = request.files.get("proof_image")
        if not proof_file:
            return error_response("Proof image required", status=400)

        filename = f"team{team_id}_{int(time.time())}_{secure_filename(proof_file.filename)}"
        save_dir = os.path.join("/app", "uploads/proof_txn")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        proof_file.save(save_path)

        BLOCKCHAIN_API = os.environ.get("BLOCKCHAIN_API_URL")

        resp = post(BLOCKCHAIN_API, json={"teamId": int(team_id)})
        if resp.status_code != 200:
            return error_response(f"Blockchain error: {resp.json().get('error')}", status=500)
        
        data = resp.json()
        tx_hash = data.get("txHash")
        txn_hash_name = data.get("fileName")
        block_number = data.get("blockNumber")

        team.is_finalized = True
        team.date_updated = now_jakarta()
        
        proof_txn = ProofTransaction(
            team_id=team.team_id,
            competition_id=team.competition_id,
            block_number=block_number,
            txn_hash=tx_hash,
            txn_hash_path=txn_hash_name,
            status=data.get("status"),
            date_created=now_jakarta(),
            date_updated=now_jakarta(),
            proof_image_path=filename
        )
        
        list_request_user = TeamJoin.query.filter(TeamJoin.team_id == team.team_id, TeamJoin.status == "P").all()
        for request_user in list_request_user:
            request_user.status = "C"
            request_user.date_updated = now_jakarta()
            
        list_invited_user = TeamInvitation.query.filter(TeamInvitation.inviter_id == team.leader_id, TeamInvitation.status == "P").all()
        for invitation in list_invited_user:
            invitation.status = "C"
            invitation.date_updated = now_jakarta()

        db.session.add(proof_txn)
        db.session.commit()

        return success_response("Team finalized successfully on-chain", data={
            "team_name": team.team_name,
            "txn_hash": tx_hash,
            "proof_path": f"uploads/proof_txn/{filename}",}, status=200)
    
    except Exception as e:
        return error_response(f"Error finalizing team: {str(e)}", status=500)
    
@team_bp.route("/request-join-team", methods=["POST"])
def request_join_team():
    try:
        req = request.get_json()
        query = Teams.query
        current_user = get_current_user_object()
        
        team = query.filter(Teams.team_id == req['team_id']).first()
        
        if team is None:
            return error_response("Team not found", status=404)
        
        new_join_request = TeamJoin(
            team_id = team.team_id,
            user_id = current_user.user_id,
            status = "P",
            date_created = now_jakarta(),
            date_updated = now_jakarta(),
        )

        db.session.add(new_join_request)
        db.session.commit()
        
        team_leader = Users.query.get(team.leader_id)
        requester = Users.query.get(current_user.user_id)
        
        if team_leader and requester: 
            try:
                msg = Message(
                    subject = "Request to Join Team",
                    recipients = [team_leader.email],
                    body = (
                        f"Hello {team_leader.username},\n\n"
                        f"{requester.username} has requested to join your team.\n\n"
                        f"Please review the request on Teammates List tab.\n\n"
                        f"Best regards,\{requester.username}"
                    ),
                    html=(
                        f"<p>Hello {team_leader.username},</p>"
                        f"<p><b>{requester.username}</b> has requested to join your team.</p>"
                        f"<p>Please review the request on <b>Teammates List tab</b>.</p>"
                        f"<p>Best regards,<br><b>{requester.username}</b></p>"
                    )
                )

                threading.Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

            except Exception as mail_error:
                print("Email not sent!")

        return success_response("Request to join team sent successfully", status=200)

    except Exception as e:
        return error_response(f"Error sending request: {str(e)}", status=500)
    
@team_bp.route("/accept-join-request", methods=["POST"])
def accept_join_request():
    try:
        req = request.get_json()
        query = TeamJoin.query
        team_query = Teams.query

        join_request = query.filter(
            (TeamJoin.team_id == req['team_id']) & (TeamJoin.user_id == req['user_id']) & (TeamJoin.status == "P")
        ).first()

        if join_request is None:
            return error_response("Join request not found", status=404)

        team = team_query.filter(Teams.team_id == req['team_id']).first()
        
        if team is None:
            return error_response("Team not found", status=404)
        
        member_ids = team.member_id.split(",") if team.member_id else []
        
        if str(req['user_id']) in member_ids:
            return error_response("User is already a member of the team", status=400)
        
        member_ids.append(str(req['user_id']))
        team.member_id = ",".join(member_ids)
        team.date_updated = now_jakarta()
        
        join_request.status = "A"
        join_request.date_updated = now_jakarta()

        db.session.commit()

        return success_response("Join request accepted successfully", status=200)

    except Exception as e:
        return error_response(f"Error accepting join request: {str(e)}", status=500)
    
@team_bp.route("/reject-join-request", methods=["POST"])
def reject_join_request():
    try:
        req = request.get_json()
        current_user = get_current_user_object()
        query = TeamJoin.query

        join_request = query.filter(
            (TeamJoin.team_id == req['team_id']) & (TeamJoin.user_id == req['user_id']) & (TeamJoin.status == "P")
        ).first()

        if join_request is None:
            return error_response("Join request not found", status=404)

        join_request.status = "R"
        join_request.date_updated = now_jakarta()

        db.session.commit()
        
        requester = Users.query.get(req['user_id'])
        team_leader = Users.query.get(current_user.user_id)
        
        if team_leader and requester: 
            try:
                msg = Message(
                    subject = "Join Request Rejected",
                    recipients = [requester.email],
                    body = (
                        f"Hello {requester.username},\n\n"
                        f"Your request to join the team has been rejected.\n\n"
                        f"Best regards,\n{team_leader.username}"
                    ),
                    html=(
                        f"<p>Hello {requester.username},</p>"
                        f"<p>Your request to join the team has been rejected.</p>"
                        f"<p>Best regards,<br><b>{team_leader.username}</b></p>"
                    )
                )

                threading.Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

            except Exception as mail_error:
                print("Email not sent!")

        return success_response("Join request rejected successfully", status=200)

    except Exception as e:
        return error_response(f"Error rejecting join request: {str(e)}", status=500)
        
@team_bp.route("/get-all-pending-request", methods=["POST"])
def get_all_pending_request():
    try:
        req = request.get_json()
        query = TeamJoin.query
        team_query = Teams.query

        team = team_query.filter(Teams.team_id == req['team_id']).first()
        
        if team is None:
            return error_response("Team not found", status=404)
        
        pending_requests = query.filter(
            (TeamJoin.team_id == team.team_id) & (TeamJoin.status == "P")
        ).all()

        results = []
        for pending in pending_requests:
            user = Users.query.get(pending.user_id)
            if user:
                results.append({
                    "user_id": user.user_id,
                    "fullname": user.fullname,
                    "email": user.email,
                    "semester": user.semester,
                    "field_of_preference": user.field_of_preference,
                    "status": pending.status,
                    "portfolio": user.portfolio,
                })

        return success_response("Pending requests retrieved successfully", data=results, status=200)

    except Exception as e:
        return error_response(f"Error fetching pending requests: {str(e)}", status=500)
        
@team_bp.route("/add-wishlist-competition", methods=["POST"])
def add_wishlist_competition():
    try:
        current_user = get_current_user_object()
        current_user_id = str(current_user.user_id)
        req = request.get_json()
        query = Teams.query

        current_team = query.filter(
            Teams.member_id.ilike(f"%{current_user_id}%")
        ).first()

        if current_team is None:
            return error_response("Team not found", status=404)
        
        competition = Competition.query.get(req["competition_id"])

        if competition.date < now_jakarta():
            return error_response("Cannot join a competition that has already started / expired", status=400)
        
        current_team.competition_id = req["competition_id"]

        db.session.commit()

        return success_response("Competition successfully added to wishlist", status=200)

    except Exception as e:
        return error_response(f"Error searching users: {str(e)}", status=500)