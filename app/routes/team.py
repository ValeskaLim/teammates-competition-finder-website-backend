from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
from app.extensions import db
from app.models import Competition, TeamInvitation, Teams, Users
from app.routes.generic import get_current_user_object, now_jakarta
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
    
@team_bp.route("/request-join", methods=["POST"])
def request_join():
    try:
        req = request.get_json()
        query = Teams.query
        current_user = get_current_user_object()
        
        team = query.filter(Teams.team_id == req['team_id']).first()
        
        if team is None:
            return error_response("Team not found", status=404)
        
        
        
    except Exception as e:
        return error_response(f"Error sending request: {str(e)}", status=500)
        
        
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