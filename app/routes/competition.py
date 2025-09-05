from flask import Blueprint, jsonify, request
from datetime import datetime
from app.extensions import db
from app.models import Competition, TeamInvitation
from app.routes.generic import get_current_user_object
from app.utils.response import success_response, error_response

competition_bp = Blueprint('competition', __name__, url_prefix="/competition")

@competition_bp.route("/get-all-competition", methods=["POST"])
def get_all_competition():
    try:
        competitions = Competition.query.all()

        return success_response("Competitions retrieved successfully", data=[c.to_dict() for c in competitions], status=200)

    except Exception as e:
        return error_response(f"Error fetch competitions: {str(e)}", status=500)

@competition_bp.route("/get-existing-competition", methods=["POST"])
def get_existing_competition():
    req = request.get_json()

    existing_data = Competition.query.filter(
        (Competition.title == req["title"])
    ).first()

    if existing_data:
        return error_response("Competition with this title already exists", status=406)
    else:
        return success_response("Competition does not exist", status=200)

@competition_bp.route("/get-competition-by-id", methods=['POST'])
def get_competititon_by_id():
    try:
        data = request.get_json()
        query = Competition.query

        competition = query.filter(Competition.competition_id == data['id']).first()

        if competition is None:
            return error_response("Competition not found", status=404)

        return success_response("Competition retrieved successfully", data=competition.to_dict(), status=200)

    except Exception as e:
        return error_response(f"Error fetching competition: {str(e)}", status=500)
        
@competition_bp.route("/add", methods=["POST"])
def add_competition():
    try:
        req = request.get_json()

        required_fields = ["title", "date", "status", "description", "type", "slot"]

        for field in required_fields:
            if field not in req or req[field] == "":
                return error_response(f"Missing or empty required field: {field[0].upper() + field[1:]}", status=400)

        if req["slot"] <= 0:
            return error_response("Slot must be greater than zero", status=406)
        
        if len(req["description"]) > 500:
            return error_response("Description cannot exceed 500 characters", status=406)

        new_competition = Competition(
            title = req["title"],
            date = req["date"],
            status = req["status"],
            description = req["description"],
            type = req["type"],
            slot = req["slot"],
            date_created = datetime.now(),
            date_updated = datetime.now(),
        )

        db.session.add(new_competition)
        db.session.commit()

        return success_response("Competition created successfully", data=new_competition.to_dict(), status=200)

    except Exception as e:
        return error_response(f"Error adding competition: {str(e)}", status=500)


    except Exception as e:
        return error_response(f"Error adding competition: {str(e)}", status=500)
        
@competition_bp.route("/remove-competition", methods=["POST"])
def remove_competition():
    try:
        data = request.get_json()
        query = Competition.query

        competition = query.filter(
            Competition.competition_id == data["competition_id"]
        ).first()

        if competition is None:
            return error_response("Competition not found", status=404)

        db.session.delete(competition)
        db.session.commit()

        return success_response(f"Success deleting competition {competition.title}", status=200)

    except Exception as e:
        return error_response(f"Error deleting competition: {str(e)}", status=500)

@competition_bp.route("/edit-competition", methods=['POST'])
def edit_competition():
    try:
        data = request.get_json()
        query = Competition.query

        current_competition = query.filter(
            Competition.competition_id == data['competition_id']
        ).first()

        if current_competition is None:
            return error_response("Competition not found", status=404)

        current_competition.title = data['title']
        current_competition.date = data['date']
        current_competition.status = data['status']
        current_competition.type = data['type']
        current_competition.slot = data['slot']
        current_competition.description = data['description']
        current_competition.date_updated = datetime.now()


        with db.session.no_autoflush:
            existing_competititon = query.filter(
                Competition.title == data['title'], 
                Competition.competition_id != data['competition_id']
            ).first()

        if existing_competititon:
            return error_response("Competition with the same title already exists", status=406)

        db.session.commit()

        return success_response("Success edit competition", data=current_competition.to_dict(), status=200)

    except Exception as e:
        return error_response(f"Error edit competition: {str(e)}", status=500)