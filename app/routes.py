from flask import Blueprint, request, jsonify, render_template, make_response, session
from app import db
from app.models import Users, Competition, Teams, TeamInvitation
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from flask_cors import CORS
import jwt
from app.similarity import filter_available_user, normalize_user, cosine_similarity


main = Blueprint("main", __name__)


def get_current_user_object():
    user_id = session.get("user_id")

    if not user_id:
        token = request.cookies.get("access_token")
        if token:
            try:
                payload = jwt.decode(token, "secret", algorithms=["HS256"])
                user_id = payload["user_id"]
                session["user_id"] = user_id
            except jwt.ExpiredSignatureError:
                return None
            except jwt.InvalidTokenError:
                return None

    if not user_id:
        return None

    return Users.query.get(user_id)


@main.route("/api/user/get-all-user", methods=["POST"])
def get_users():
    try:
        query = Users.query

        return (
            jsonify(
                {
                    "success": True,
                    "data": [user.to_dict() for user in query.all()],
                    "statusCode": 200,
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error fetching users: {str(e)}"}),
            500,
        )
        
def check_is_already_have_team(user_id):
    str_user_id = str(user_id)
    query = Teams.query

    is_have_team = query.filter(
        Teams.member_id.ilike(f"%{str_user_id}%")
    ).first()

    return is_have_team is not None


@main.route("/api/auth/validate-user", methods=["POST"])
def validate_user():
    try:
        req = request.get_json()

        is_user_exist = Users.query.filter(
            (Users.email == req["email"]) & (Users.password == req["password"])
        ).first()

        if is_user_exist is None:
            return (
                jsonify({"success": False, "message": f"Invalid email or password"}),
                401,
            )

        session["user_id"] = is_user_exist.user_id
        # session.permanent = True

        token = jwt.encode(
            {
                "user_id": is_user_exist.user_id,
                "exp": datetime.utcnow() + timedelta(hours=3),
            },
            "secret",
            algorithm="HS256",
        )

        res = make_response(
            jsonify(
                {
                    "success": True,
                    "message": f"Login successful",
                    "user": {
                        "user_id": is_user_exist.user_id,
                        "username": is_user_exist.username,
                        "email": is_user_exist.email,
                        "fullname": is_user_exist.fullname,
                    },
                }
            )
        )

        res.set_cookie(
            "access_token",
            token,
            httponly=True,
            secure=True,
            samesite="None",
            max_age=60 * 60,
        )

        return res

    except Exception as e:
        return jsonify({"success": False, "message": f"Error validating user"}), 500


@main.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    res = make_response(jsonify({"message": "Logges out"}))
    res.set_cookie("access_token", "", expires=0, samesite="None", secure=True)

    res.set_cookie("session", "", expires=0, samesite="None", secure=True)
    return res


@main.route("/api/user/get-current-user", methods=["POST"])
def get_current_user():

    user = get_current_user_object()
    if not user:
        return jsonify({"user": None}), 200

    return (
        jsonify(
            {
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "fullname": user.fullname,
                    "gender": user.gender,
                    "semester": user.semester,
                    "role": user.role,
                    "field_of_preference": user.field_of_preference,
                    "major": user.major,
                }
            }
        ),
        200,
    )


@main.route("/api/user/get-existing-user", methods=["POST"])
def get_existing_user():
    try:
        req = request.get_json()

        query = Users.query

        existing_username = query.filter((Users.username == req["username"])).first()

        existing_email = query.filter(Users.email == req["email"]).first()

        return (
            jsonify(
                {
                    "success": True,
                    "usernameExist": existing_username is not None,
                    "emailExist": existing_email is not None,
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error getting user: {str(e)}"}),
            500,
        )


@main.route("/api/user/submit-register-data", methods=["POST"])
def create_user():
    try:
        data = request.get_json()

        # List of required fields
        required_fields = [
            "username",
            "password",
            "email",
            "fullname",
            "gender",
            "semester",
            "field_of_preference",
        ]

        # Validate empty fields
        for field in required_fields:
            if field not in data or data[field] == "":
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": f"Missing or empty required field: {field[0].upper() + field[1:]}",
                        }
                    ),
                    400,
                )

        if " " in data["username"]:
            return (
                jsonify(
                    {"success": False, "message": "Username cannot contain spaces"}
                ),
                400,
            )

        # Validate email format and password length
        if data["email"].find("@") == -1:
            return jsonify({"success": False, "message": "Invalid email format"}), 400

        if len(data["password"]) < 4:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Password must be at least 4 characters long",
                    }
                ),
                400,
            )

        # Check for existing username or email
        existing_user = Users.query.filter(
            (Users.username == data["username"]) | (Users.email == data["email"])
        ).first()

        if existing_user:
            return (
                jsonify(
                    {"success": False, "message": "Username or email already exists"}
                ),
                400,
            )

        new_user = Users(
            username=data["username"],
            password=data["password"],
            email=data["email"],
            role="normal",
            fullname=data["fullname"],
            gender=data["gender"],
            semester=data["semester"],
            major="Computer Science",
            field_of_preference=data["field_of_preference"],
            date_created=datetime.now(),
            date_updated=datetime.now()
        )

        db.session.add(new_user)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "User created successfully",
                    "user_id": new_user.user_id,
                    "user": new_user.to_dict(),
                }
            ),
            201,
        )

    except IntegrityError:
        db.session.rollback()
        return (
            jsonify({"success": False, "message": "Username or email already exists"}),
            400,
        )
    except KeyError as e:
        return (
            jsonify({"success": False, "message": f"Missing required field: {str(e)}"}),
            400,
        )
    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"success": False, "message": f"Error creating user: {str(e)}"}),
            500,
        )


@main.route("/api/competition/get-all-competition", methods=["POST"])
def get_all_competition():
    try:
        competitions = Competition.query.all()

        return (
            jsonify({"success": True, "data": [c.to_dict() for c in competitions]}),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {"success": False, "message": f"Error fetch competitions: {str(e)}"}
            ),
            500,
        )


@main.route("/api/competition/add", methods=["POST"])
def add_competition():
    try:
        req = request.get_json()

        required_fields = ["title", "date", "status", "description", "type", "slot"]

        for field in required_fields:
            if field not in req or req[field] == "":
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": f"Missing or empty required field: {field[0].upper() + field[1:]}",
                        }
                    ),
                    400,
                )

        if req["slot"] <= 0:
            return jsonify({
                    "success": False, 
                    "message": "Slot must be greater than zero"
                }), 500
        
        if len(req["description"]) > 500:
            return jsonify({
                    "success": False, 
                    "message": "Description cannot exceed 500 characters"
                }), 400

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

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Competition created successfully",
                    "competition_id": new_competition.competition_id,
                    "data": new_competition.to_dict(),
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {"success": False, "message": f"Error adding competition: {str(e)}"}
            ),
            500,
        )


@main.route("/api/competition/get-existing-competition", methods=["POST"])
def get_existing_competition():
    req = request.get_json()

    existing_data = Competition.query.filter(
        (Competition.title == req["title"])
    ).first()

    if existing_data:
        return jsonify({"success": True, "isExist": True}), 200
    else:
        return jsonify({"success": True, "isExist": False}), 200
    
@main.route("/api/competition/get-competition-by-id", methods=['POST'])
def get_competititon_by_id():
    try:
        data = request.get_json()
        query = Competition.query

        competition = query.filter(Competition.competition_id == data['id']).first()

        if competition is None:
            return jsonify({
                'success': False,
                'message': 'Data not found'
            }, 500)
        
        return jsonify({
            'success': True,
            'data': competition.to_dict()
        })

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error fetching competition: {str(e)}"}),
            500,
        )
    
@main.route("/api/competition/edit-competition", methods=['POST'])
def edit_competition():
    try:
        data = request.get_json()
        query = Competition.query

        current_competition = query.filter(
            Competition.competition_id == data['competition_id']
        ).first()

        if current_competition is None:
            return jsonify({
                'success': False,
                'message': 'Data not found'
            }), 500
        
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
            return jsonify({
                'success': False,
                'message': 'Competition with the same title already exists'
            }), 406

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Success edit competititon'
        }), 200

    except Exception as e:
        return (
            jsonify({
                "success": False, 
                "message": f"Error edit competition: {str(e)}"
            }), 500
        )

@main.route("/api/user/edit-user", methods=["POST"])
def edit_user():
    try:
        data = request.get_json()
        query = Users.query

        if " " in data["username"]:
            return jsonify({
                "success": False, 
                "message": "Username cannot contain spaces"
            }), 400

        if data["email"].find("@") == -1:
            return jsonify({"success": False, "message": "Invalid email format"}), 400

        user = query.filter_by(user_id=data["user_id"]).first()
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # with db.session.no_autoflush:
        existing_username = query.filter(
            Users.username.ilike(f"%{data['username']}%"),
            Users.user_id != data['user_id']
        ).first()
        
        existing_email = query.filter(
            Users.email == data['email'],
            Users.user_id != data['user_id']
        ).first()

        if existing_username or existing_email:
            return jsonify({
                'success': False,
                'message': 'Username or email already exist'
            }), 500

        user.username = data["username"],
        user.email = data["email"],
        user.gender = data["gender"],
        user.semester = data["semester"],
        user.field_of_preference = data["field_of_preference"]
        user.date_updated=datetime.now()

        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Edit user successfully",
                    "user": user.to_dict(),
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error editing user: {str(e)}"}),
            500,
        )

@main.route("/api/user/get-user-by-id", methods=["POST"])
def get_user_by_id():
    try:
        req = request.get_json()
        query = Users.query

        user = query.filter(
            Users.user_id == req["user_id"]
        ).first()

        if user is None:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        return jsonify({
            "success": True,
            "data": user.to_dict()
        }), 200

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error fetching user: {str(e)}"}),
            500,
        )
    
@main.route("/api/user/check-is-have-team", methods=["POST"])
def check_is_have_team():
    try:
        current_user = get_current_user_object()
        query = Teams.query

        is_have_team = query.filter(
            Teams.member_id.ilike(f"%{current_user.user_id}%")
        ).first()

        if is_have_team is None:
            return jsonify({
                "success": False,
                "message": "User doesn't have team yet"
            }), 200
        
        return jsonify({
            "success": True,
            "message": "User registered in team"
        })

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error checking: {str(e)}"}),
            500,
        )


@main.route("/api/user/get-all-teammates", methods=["POST"])
def get_all_teammates():
    try:
        current_user = get_current_user_object()

        if not current_user:
            return (
                jsonify(
                    {"success": False, "message": "Unauthorized or user not found"}
                ),
                401,
            )

        team_member = Teams.query.filter(
            Teams.member_id.ilike(f"%{current_user.user_id}%")
        ).first()

        if team_member is None:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
        
        return jsonify({
            "success": True,
            "data": team_member.to_dict()
        }), 200

    except Exception as e:
        return (
            jsonify(
                {"success": False, "message": f"Error fetching teammates: {str(e)}"}
            ),
            500,
        )


@main.route("/api/user/remove-user-teammates", methods=["POST"])
def remove_user():
    try:
        data = request.get_json()
        target_user_id = str(data.get("user_id"))
        query = Teams.query

        if not target_user_id:
            return jsonify({"success": False, "message": "User ID is required"}), 400

        current_user = get_current_user_object()
        if not current_user:
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        member_to_delete = query.filter(
            Teams.member_id.ilike(f"%{target_user_id}%")
        ).first()

        if not member_to_delete:
            return (
                jsonify(
                    {"success": False, "message": "This member doesnt exist in the team"}
                ),
                404,
            )
        
        member_ids = member_to_delete.member_id.split(",")

        if str(target_user_id) in member_ids:
            member_ids.remove(str(target_user_id))

        member_to_delete.member_id = ",".join(member_ids)

        member_to_delete.date_updated = datetime.now()

        db.session.commit()

        return (
            jsonify(
                {"success": True, "message": f"Success removed user {target_user_id}"}
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error deleting user: {str(e)}"}),
            500,
        )

@main.route("/api/recommend", methods=["POST"])
def recommend():
    req = request.get_json()
    
    # Check user is already have team
    is_have_team = check_is_already_have_team(req["user_id"])
    
    if is_have_team is False:
        return jsonify({
            "success": False,
            "message": "User doesn't have team yet, please create or join team first"
        }), 500
    
    target_user_record = Users.query.filter_by(user_id=req["user_id"]).first()
    if not target_user_record:
        return jsonify({
            "success": False, 
            "message": "User not found"
        }), 404

    target_user = {
        "id": target_user_record.user_id,
        "semester": target_user_record.semester,
        "gender": "L" if target_user_record.gender == "L" else "P",
        "field_of_preference": [f.strip() for f in target_user_record.field_of_preference.split(",") if f.strip()]
    }
    
    users = filter_available_user(req["user_id"])

    print('users:',users)
    
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
    
    return jsonify({
        "success": True,
        "results": results[:5]
    }), 200



@main.route("/api/user/search", methods=["POST"])
def search_users():
    try:
        data = request.get_json()
        query = Users.query

        if "major" in data and data["major"]:
            query = query.filter(Users.major.ilike(f"%{data['major']}%"))

        if "semester" in data and data["semester"]:
            query = query.filter(Users.semester == data["semester"])

        if "gender" in data and data["gender"]:
            query = query.filter(Users.gender == data["gender"])

        if "field_of_preference" in data and data["field_of_preference"]:
            query = query.filter(
                Users.field_of_preference.ilike(f"%{data['field_of_preference']}%")
            )

        page = data.get("page", 1)
        per_page = data.get("per_page", 10)

        users = query.paginate(page=page, per_page=per_page, error_out=False)

        return (
            jsonify(
                {
                    "success": True,
                    "users": [user.to_dict() for user in users.items],
                    "total": users.total,
                    "pages": users.pages,
                    "current_page": users.page,
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error searching users: {str(e)}"}),
            500,
        )


@main.route("/api/competition/remove-competition", methods=["POST"])
def remove_competition():
    try:
        data = request.get_json()
        query = Competition.query

        competition = query.filter(
            Competition.competition_id == data["competition_id"]
        ).first()

        if competition is None:
            return jsonify({
                "success": False, "message": "Competition not found"
            }), 404

        db.session.delete(competition)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Success deleting competition {competition.title}",
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error searching users: {str(e)}"}),
            500,
        )

@main.route("/api/user/get-invitees-user", methods=["POST"])
def get_invitees_user():
    try:
        user = get_current_user_object()
        query = TeamInvitation.query
        
        invited_user = query.filter(
            TeamInvitation.inviter_id == user.user_id, TeamInvitation.status == "P"
        ).all()

        
        if invited_user is None or invited_user == []:
            return jsonify({
                "success": True, 
                "message": "Invitation not found"
            }), 200
        
        return jsonify({
            "success": True,
            "data": [user.to_dict() for user in invited_user]
        }), 200
        
        
    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error fetching users: {str(e)}"}),
            500,
        )

@main.route("/api/user/get-invites-user", methods=["POST"])
def get_invites_user():
    try:
        current_user = get_current_user_object()

        query = TeamInvitation.query

        invitation_list = query.filter(
            TeamInvitation.invitee_id == current_user.user_id, TeamInvitation.status == "P"
        ).all()

        if invitation_list is None or invitation_list == []:
            return jsonify({
                "success": False,
                "message": "Invitation not found"
            }), 200

        return jsonify({
            "success": True,
            "data": [user.to_dict() for user in invitation_list]
        }), 200

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error fetching users: {str(e)}"}),
            500,
        )
    
@main.route("/api/user/accept-invites", methods=["POST"])
def accept_invites():
    try:
        current_user = get_current_user_object()
        req = request.get_json()
        query = TeamInvitation.query

        team_invitation = query.filter(
            TeamInvitation.inviter_id == req["user_id"]
        ).first()

        if team_invitation is None:
            return jsonify({
                "success": False,
                "message": "Invites not found"
            }), 404
        
        if team_invitation == "A":
            return jsonify({
                "success": False,
                "message": "Cannot accept invites with status Active"
            }), 500
        
        team_invitation.status = "A"
        team_invitation.date_updated = datetime.now()

        get_inviter_team = Teams.query.filter(
            Teams.member_id.ilike(f"%{req['user_id']}%")
        ).first()

        if get_inviter_team is None:
            return jsonify({
                "success": False,
                "message": "Team not found"
            }), 404
        
        get_inviter_team.member_id += f",{current_user.user_id}"

        db.session.commit()

        return jsonify({
            "success": True,
            "messages": "Invites successfully accepted"
        }), 200

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error fetching users: {str(e)}"}),
            500,
        )
    
@main.route("/api/user/reject-invites", methods=["POST"])
def reject_invites():
    try:
        req = request.get_json()
        query = TeamInvitation.query

        invitation_to_remove = query.filter(
            TeamInvitation.inviter_id == req["user_id"]
        ).first()

        if invitation_to_remove is None:
            return jsonify({
                "success": False,
                "message": "Invites not found"
            }), 404
        
        if invitation_to_remove == "A":
            return jsonify({
                "success": False,
                "message": "Cannot reject invites with status Active"
            }), 500
        
        db.session.delete(invitation_to_remove)
        db.session.commit()

        return jsonify({
                "success": True,
                "messages": "Invites successfully removed"
            }), 200

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error fetching users: {str(e)}"}),
            500,
        )
    
@main.route("/api/team/create-team", methods=["POST"])
def create_team():
    try:
        req = request.get_json()
        query = Teams.query

        check_is_exist = query.filter(
            (Teams.team_name == req['team_name']) | (Teams.leader_id == req['leader_id'])
        ).first()

        if check_is_exist is not None:
            return jsonify({
                "success": False,
                "message": "Team / user already exist"
            }), 500
        
        new_team = Teams(
            member_id = str(req["leader_id"]),
            team_name = req["team_name"],
            date_created = datetime.now(),
            date_updated = datetime.now(),
            leader_id = req["leader_id"],
        )

        db.session.add(new_team)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Team  successfully created"
        }), 200

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error fetching users: {str(e)}"}),
            500,
        )
    
@main.route("/api/team/add-wishlist-competition", methods=["POST"])
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
            return jsonify({
                "success": False,
                "message": "Team not found"
            }), 404
        
        if current_team.competition_id is not None:
            return jsonify({
                "success": False,
                "message": "Each team only allowed to join 1 competition"
            }), 500
        
        current_team.competition_id = req["competition_id"]

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Competition successfully added to wishlist"
        }), 200

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error searching users: {str(e)}"}),
            500,
        )
    
@main.route("/api/team/remove-wishlist-competition", methods=["POST"])
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
            return jsonify({
                "success": True,
                "message": "Team not found"
            }), 404
        
        current_team.competition_id = None

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Competition successfully removed from wishlist"
        }), 200

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error searching users: {str(e)}"}),
            500,
        )
    
@main.route("/api/team/check-is-leader", methods=["POST"])
def check_is_leader():
    try:
        current_user = get_current_user_object()
        query = Teams.query

        is_leader = query.filter(
            Teams.leader_id == current_user.user_id, Teams.member_id.ilike(f"%{current_user.user_id}%")
        ).first()

        if is_leader is None:
            return({
                "success": True,
                "isLeader": False
            }), 200
        
        return jsonify({
            "success": True,
            "isLeader": True
        }), 200

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error fetching users: {str(e)}"}),
            500,
        )