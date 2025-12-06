from app.extensions import db
from flask import Blueprint, request, jsonify
from app.models import Users, Teams, UserSkillsMapping, Skills
from app.routes.generic import get_current_user_object, check_is_already_have_team
from app.utils.response import success_response, error_response

find_bp = Blueprint('find', __name__, url_prefix="/find")

@find_bp.route("/filter-users-by-skill", methods=["POST"])
def filter_users_by_skill():
    try:
        req = request.get_json()
        required_skills = req.get("skills", [])
        current_user = get_current_user_object()
        users = Users.query.all()
        team_query = Teams.query
        
        team_users = set()

        teams = team_query.all()
        for team in teams:
            if team.leader_id:
                team_users.add(team.leader_id)

            if team.member_id:
                member_ids = [int(x) for x in team.member_id.split(",") if x.strip().isdigit()]
                team_users.update(member_ids)

        eligible_users = [u for u in users if u.user_id not in team_users and u.user_id != current_user.user_id and u.is_verified]
        
        filtered = []
        for u in eligible_users:
            skills = (
                db.session.query(Skills.skill_id, Skills.skill_name)
                .join(UserSkillsMapping, UserSkillsMapping.skill_id == Skills.skill_id)
                .filter(UserSkillsMapping.user_id == u.user_id)
                .all()
            )
            skill_list = [
                {"skill_id": s.skill_id, "skill_name": s.skill_name}
                for s in skills
            ]
            required_skill_ids = {int(s) for s in required_skills}
            user_skill_ids = {int(s["skill_id"]) for s in skill_list}
            if required_skill_ids.issubset(user_skill_ids):
                filtered.append({
                    "user_id": u.user_id,
                    "username": u.username,
                    "fullname": u.fullname,
                    "email": u.email,
                    "semester": u.semester,
                    "skills": skill_list,
                })

        return success_response("Filtered users retrieved", data=filtered)
        
    except Exception as e:
        return error_response(f"Error retrieving users: {str(e)}", status=500)
    
@find_bp.route("/get-all-users", methods=["POST"])
def get_all_users():
    try:
        users = Users.query.all()
        team_query = Teams.query
        current_user = get_current_user_object()
        
        team_users = set()

        teams = team_query.all()
        for team in teams:
            if team.leader_id:
                team_users.add(team.leader_id)

            if team.member_id:
                member_ids = [int(x) for x in team.member_id.split(",") if x.strip().isdigit()]
                team_users.update(member_ids)

        filtered_users = [u for u in users if u.user_id not in team_users and u.user_id != current_user.user_id]
        
        for u in filtered_users:
            skills = (
                db.session.query(Skills.skill_id, Skills.skill_name)
                .join(UserSkillsMapping, UserSkillsMapping.skill_id == Skills.skill_id)
                .filter(UserSkillsMapping.user_id == u.user_id)
                .all()
            )
            skill_list = [
                {"skill_id": s.skill_id, "skill_name": s.skill_name}
                for s in skills
            ]

        user_data = [{
            "user_id": u.user_id,
            "username": u.username,
            "fullname": u.fullname,
            "email": u.email,
            "semester": u.semester,
            "portfolio": u.portfolio,
            "skills": skill_list
        } for u in filtered_users]

        return success_response("All users retrieved", data=user_data)
    
    except Exception as e:
        return error_response(f"Error retrieving users: {str(e)}", status=500)