from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
from app.extensions import db
from app.models import Teams, Users
from app.routes.generic import get_current_user_object
from flask_mail import Message
import threading
from app.routes.generic import send_async_email
from app.utils.response import success_response, error_response

team_bp = Blueprint('team', __name__, url_prefix="/team")

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
            date_created = datetime.now(),
            date_updated = datetime.now(),
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
        
        if req["team_name"] == "":
            return error_response("Team name is required", status=406)

        current_team = query.filter(
            Teams.team_id == req["team_id"]
        ).first()
        
        current_team.team_name = req["team_name"]
        current_team.date_updated = datetime.now()

        db.session.commit()

        return success_response("Team successfully edited", status=200)

    except Exception as e:
        return error_response(f"Error editing team: {str(e)}", status=500)
        
@team_bp.route("/delete-team", methods=["POST"])
def delete_team():
    try:
        req = request.get_json()
        query = Teams.query
        
        current_team = query.filter(
            Teams.leader_id == req["user_id"]
        ).first()
        
        if current_team is None:
            return error_response("Team not found or you are not the leader", status=404)

        member_ids = []
        if current_team.member_id:
            member_ids = [int(mid.strip()) for mid in current_team.member_id.split(",") if mid.strip().isdigit()]
            
        team_name = current_team.team_name
            
        db.session.delete(current_team)
        db.session.commit()
        
        # Notify all team members by email
        members = Users.query.filter(Users.user_id.in_(member_ids)).all()

        for member in members:
            if member and member.email:
                try:
                    msg = Message(
                        subject="Team Disbanded",
                        recipients=[member.email],
                        body=(
                            f"Hello {member.username},\n\n"
                            f"We regret to inform you that your team {team_name}, has been disbanded by the leader.\n\n"
                            f"Best regards,\nYour Team"
                        ),
                        html=(
                            f"<p>Hello {member.username},</p>"
                            f"<p>We regret to inform you that your team <b>{team_name}</b>, has been <b>disbanded</b> by the leader.</p>"
                            f"<p>Best regards,<br><b>Your Team</b></p>"
                        )
                    )
                    threading.Thread(
                        target=send_async_email,
                        args=(current_app._get_current_object(), msg)
                    ).start()

                except Exception as mail_error:
                    print(f"Email not sent to {member.username} ({member.email}): {mail_error}")
        
        return success_response("Team successfully deleted", status=200)
        
    except Exception as e:
        return error_response(f"Error deleting team: {str(e)}", status=500)
    
@team_bp.route("/leave-team", methods=["POST"])
def leave_team():
    try:
        current_user = get_current_user_object()
        current_user_str = str(current_user.user_id)
        query = Teams.query

        current_team = query.filter(
            Teams.member_id.ilike(f"%{current_user_str}%")
        ).first()

        if current_team is None:
            return error_response("Team not found", status=404)

        if current_team.leader_id == current_user.user_id:
            return error_response("Leader cannot leave the team, please delete the team instead", status=406)

        member_ids = [mid.strip() for mid in current_team.member_id.split(",") if mid.strip().isdigit()]
        
        if current_user_str in member_ids:
            member_ids.remove(current_user_str)
            current_team.member_id = ",".join(member_ids)
            current_team.date_updated = datetime.now()
            db.session.commit()
            
            # Notify all team members by email
            members = Users.query.filter(Users.user_id.in_(member_ids)).all()

            for member in members:
                if member and member.email:
                    try:
                        msg = Message(
                            subject="Someone Left the Team",
                            recipients=[member.email],
                            body=(
                                f"Hello {member.username},\n\n"
                                f"{current_user.username} has left the team {current_team.team_name}.\n\n"
                                f"Please check your team members list for updated information.\n\n"
                                f"Best regards,\nYour Team"
                            ),
                            html=(
                                f"<p>Hello {member.username},</p>"
                                f"<p><b>{current_user.username}</b> has left the team <b>{current_team.team_name}</b>.</p>"
                                f"<p>Please check your team members list for updated information.</p>"
                                f"<p>Best regards,<br><b>Your Team</b></p>"
                            )
                        )
                        threading.Thread(
                            target=send_async_email,
                            args=(current_app._get_current_object(), msg)
                        ).start()

                    except Exception as mail_error:
                        print(f"Email not sent to {member.username} ({member.email}): {mail_error}")

            return success_response("Successfully left the team", status=200)
        else:
            return error_response("You are not a member of this team", status=500)
        
        
    except Exception as e:
        return error_response(f"Error leaving team: {str(e)}", status=500)
        
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
        
@team_bp.route("/remove-wishlist-competition", methods=["POST"])
def remove_wishlist_competition():
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

        current_team.competition_id = None

        db.session.commit()

        return success_response("Competition successfully removed from wishlist", status=200)

    except Exception as e:
        return error_response(f"Error searching users: {str(e)}", status=500)