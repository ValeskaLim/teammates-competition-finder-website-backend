from flask import Blueprint, jsonify, request, send_from_directory
from datetime import datetime
from app.extensions import db
from app.models import Competition, TeamInvitation, Teams, Users, CompetitionCategory
from app.routes.generic import MAX_CONTENT_LENGTH, UPLOAD_FOLDER, allowed_file, get_current_user_object
from app.utils.response import success_response, error_response
from werkzeug.utils import secure_filename
import os
import uuid

competition_bp = Blueprint('competition', __name__, url_prefix="/competition")

@competition_bp.route("/get-all-competition", methods=["POST"])
def get_all_competition():
    try:
        competitions = Competition.query.all()

        return success_response("Competitions retrieved successfully", data=[c.to_dict() for c in competitions], status=200)

    except Exception as e:
        return error_response(f"Error fetch competitions: {str(e)}", status=500)
    
@competition_bp.route("/get-all-categories", methods=["POST"])
def get_all_categories():
    try:
        categories = CompetitionCategory.query.all()

        return success_response("Categories retrieved successfully", data=[c.to_dict() for c in categories], status=200)
    except Exception as e:
        return error_response(f"Error fetch categories: {str(e)}", status=500)

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
    
@competition_bp.route("/get-participant-by-id", methods=['POST'])
def get_participant_by_id():
    try:
        data = request.get_json()
        query = Teams.query

        teams = query.filter(Teams.competition_id == data['competition_id']).all()

        if not teams:
            return success_response("No participants found", data=[], status=200)

        results = []
        for team in teams:
            member_ids = [int(mid) for mid in team.member_id.split(",") if mid]
            members = Users.query.filter(Users.user_id.in_(member_ids)).all()
            member_list = [member.fullname for member in members]
            
            leader = Users.query.get(team.leader_id)
            leader_name = leader.fullname if leader else None
            
            results.append({
                "team_id": team.team_id,
                "team_name": team.team_name,
                "is_finalized": team.is_finalized,
                "leader_id": team.leader_id,
                "leader_name": leader_name,
                "members": member_list,
                "notes": team.notes,
                "is_full": len(member_list) >= Competition.query.get(data['competition_id']).max_member if Competition.query.get(data['competition_id']) else False
            })

        return success_response("Participants retrieved successfully", data=results, status=200)

    except Exception as e:
        return error_response(f"Error fetching participants: {str(e)}", status=500)
        
@competition_bp.route("/add", methods=["POST"])
def add_competition():
    try:
        title = request.form.get("title")
        date = request.form.get("date")
        status = request.form.get("status")
        description = request.form.get("description")
        category = request.form.get("category")
        min_member = request.form.get("min_member")
        max_member = request.form.get("max_member")
        poster = request.files.get("poster")
        original_url = request.form.get("original_url", None)
        
        min_member = int(min_member)
        max_member = int(max_member)

        required_fields = [title, date, status, description, category, min_member, max_member]
        field_names = ["Title", "Date", "Status", "Description", "Category", "Min member", "Max member"]

        for f, name in zip(required_fields, field_names):
            if not f:
                return error_response(f"Missing or empty required field: {name}", status=400)
            
        if not poster or poster.filename == "":
            return error_response("Poster is required", status=400)
            
        if not allowed_file(poster.filename):
            return error_response("Only .jpg, .jpeg, .png files are allowed", status=400)
        
        poster.seek(0, os.SEEK_END)
        if poster.tell() > MAX_CONTENT_LENGTH:
            return error_response("Poster cannot exceed 5 MB", status=400)
        poster.seek(0)

        if min_member <= 0:
            return error_response("Min member must be greater than zero", status=406)

        if max_member <= 0:
            return error_response("Max member must be greater than zero", status=406)
        
        if min_member > max_member:
            return error_response("Min member cannot be greater than max member", status=406)

        if len(description) > 4000:
            return error_response("Description cannot exceed 4000 characters", status=406)

        filename = secure_filename(os.path.basename(poster.filename))
        filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        poster.save(file_path)

        new_competition = Competition(
            title=title,
            date=date,
            status=status,
            description=description,
            category=category,
            min_member=min_member,
            max_member=max_member,
            poster=filename,
            original_url=original_url,
            date_created=datetime.now(),
            date_updated=datetime.now()
        )

        db.session.add(new_competition)
        db.session.commit()

        return success_response("Competition created successfully", data=new_competition.to_dict(), status=200)

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
        competition_id = request.form.get("competition_id")
        title = request.form.get("title")
        date = request.form.get("date")
        status = request.form.get("status")
        description = request.form.get("description")
        category = request.form.get("category")
        min_member = request.form.get("min_member")
        max_member = request.form.get("max_member")
        poster = request.files.get("poster")
        original_url = request.form.get("original_url", None)
        
        competition_id = int(competition_id)
        min_member = int(min_member)
        max_member = int(max_member)
        
        query = Competition.query

        current_competition = query.filter(
            Competition.competition_id == competition_id
        ).first()

        if current_competition is None:
            return error_response("Competition not found", status=404)
        
        if min_member <= 0 or max_member <= 0:
            return error_response("Member count must be greater than zero", status=406)

        if min_member > max_member:
            return error_response("Min member cannot be greater than max member", status=406)
        
        if len(description) > 4000:
            return error_response("Description cannot exceed 4000 characters", status=406)

        # Poster replacement is optional
        if poster and poster.filename.strip():
            if not allowed_file(poster.filename):
                return error_response("Only .jpg, .jpeg, .png files are allowed", status=400)

            poster.seek(0, os.SEEK_END)
            if poster.tell() > MAX_CONTENT_LENGTH:
                return error_response("Poster cannot exceed 5 MB", status=400)
            poster.seek(0)

            # remove old poster if exists
            if current_competition.poster:
                old_path = os.path.join(UPLOAD_FOLDER, current_competition.poster)
                if os.path.exists(old_path):
                    os.remove(old_path)
                    print("Old path: ", old_path, flush=True)

            # save new one
            filename = secure_filename(os.path.basename(poster.filename))
            filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            poster.save(file_path)

            current_competition.poster = filename

        current_competition.title = title
        current_competition.date = date
        current_competition.status = status
        current_competition.category = category
        current_competition.min_member = min_member
        current_competition.max_member = max_member
        current_competition.description = description
        current_competition.date_updated = datetime.now()
        current_competition.original_url = original_url

        with db.session.no_autoflush:
            existing_competititon = query.filter(
                Competition.title == title,
                Competition.competition_id != competition_id
            ).first()

        if existing_competititon:
            return error_response("Competition with the same title already exists", status=406)

        db.session.commit()

        return success_response("Success edit competition", data=current_competition.to_dict(), status=200)

    except Exception as e:
        return error_response(f"Error edit competition: {str(e)}", status=500)
    
@competition_bp.route("/uploads/<filename>", methods=['GET'])
def get_uploaded_file(filename):
    """
    Serve competition poster files.
    """
    print("Serving file:", os.path.join(UPLOAD_FOLDER, filename), flush=True)
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        return error_response(f"File not found: {str(e)}", status=404)