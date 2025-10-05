from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
from app.extensions import db
from app.models import Competition, TeamInvitation, TeamJoin, Teams, Users
from app.routes.generic import get_current_user_object, now_jakarta
from flask_mail import Message
import threading
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
    
@team_bp.route("/finalize-team", methods=["POST"])
def finalize_team():
    try:
        data = request.get_json()
        current_user = get_current_user_object()
        team_query = Teams.query
        team_invitation_query = TeamInvitation.query
        
        current_team = team_query.filter(
            Teams.team_id == data["team_id"]
        ).first()

        if current_team is None:
            return error_response("Team not found", status=404)
        
        invitation_to_delete = team_invitation_query.filter((TeamInvitation.inviter_id == current_user.user_id), (TeamInvitation.status == "P")).all()
        
        for invitation in invitation_to_delete:
            invitation.status = "C"
            invitation.date_updated = now_jakarta()

        current_team.is_finalized = True
        current_team.date_updated = now_jakarta()
        db.session.commit()

        return success_response("Team successfully finalized", status=200)
        
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
        query = TeamJoin.query

        join_request = query.filter(
            (TeamJoin.team_id == req['team_id']) & (TeamJoin.user_id == req['user_id']) & (TeamJoin.status == "P")
        ).first()

        if join_request is None:
            return error_response("Join request not found", status=404)

        join_request.status = "R"
        join_request.date_updated = now_jakarta()

        db.session.commit()

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
                    "status": pending.status
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

        if current_team.competition_id is not None:
            return error_response("Each team only allowed to join 1 competition", status=500)
        
        current_team.competition_id = req["competition_id"]

        db.session.commit()

        return success_response("Competition successfully added to wishlist", status=200)

    except Exception as e:
        return error_response(f"Error searching users: {str(e)}", status=500)