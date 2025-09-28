from flask import Blueprint, request, jsonify
from app.models import Users, Teams
from app.routes.generic import get_current_user_object, check_is_already_have_team
from app import similarity
from app.similarity import normalize_user, cosine_similarity, filter_available_user
from app.utils.response import success_response, error_response

recommend_bp = Blueprint('recommend', __name__, url_prefix="/recommend")

@recommend_bp.route("", methods=["POST"])
def recommend():
    req = request.get_json()
    
    # Validation to use recommend feature
    is_have_team = check_is_already_have_team(req["user_id"])
    
    if is_have_team is False:
        return error_response("You don't have a team yet, please create or join a team first", status=500)
    
    is_team_finalized = Teams.query.filter(
        Teams.leader_id == req["user_id"], Teams.is_finalized == True
    ).first()
    
    if is_team_finalized:
        return error_response("Your team is already finalized", status=500)

    is_leader = Teams.query.filter(
            Teams.leader_id == req["user_id"]
        ).first()

    if is_leader is None:
        return error_response("Only team leader can access this feature", status=406)

    target_user_record = Users.query.filter_by(user_id=req["user_id"]).first()
    if not target_user_record:
        return error_response("User not found", status=404)

    target_user = {
        "id": target_user_record.user_id,
        "semester": target_user_record.semester,
        "gender": "L" if target_user_record.gender == "L" else "P",
        "field_of_preference": [f.strip() for f in target_user_record.field_of_preference.split(",") if f.strip()]
    }
    
    users = filter_available_user(req["user_id"])
    
    semesters = [u["semester"] for u in users + [target_user]]
    min_sem = min(semesters)
    max_sem = max(semesters)

    target_vector = normalize_user(
        target_user, 
        min_sem, 
        max_sem,
        ignore_gender=req["ignore_gender"],
        ignore_semester=req["ignore_semester"]
    )

    results = []
    for user in users:
        vector = normalize_user(
            user,
            min_sem, 
            max_sem,
            ignore_gender=req["ignore_gender"],
            ignore_semester=req["ignore_semester"]
        )
        similarity = cosine_similarity(target_vector, vector)
        results.append({
            "user_id": user["id"],
            "fullname": user["fullname"],
            "username": user["username"],
            "gender": user["gender"],
            "semester": user["semester"],
            "field_of_preference": ",".join(user["field_of_preference"]),
            "similarity": similarity
        })

    results.sort(key=lambda x: x["similarity"], reverse=True)

    return success_response("Recommendations retrieved successfully", data=results[:5], status=200)