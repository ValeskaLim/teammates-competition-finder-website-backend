from flask import Blueprint, request, jsonify, render_template, make_response, session
from app import db
from app.models import Users, Competition, UserCompetition, TeamInvitation
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from flask_cors import CORS
import jwt


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

        if req["slot"] < 0:
            return (
                jsonify({"success": False, "message": "Slot cannot goes negative"}),
                400,
            )

        new_competition = Competition(
            title=req["title"],
            date=req["date"],
            status=req["status"],
            description=req["description"],
            type=req["type"],
            slot=req["slot"],
        )

        db.session.add(new_competition)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Competition created successfully",
                    "competition_id": new_competition.competition_id,
                    "data": new_competition.to_string(),
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

        if " " in data["username"]:
            return (
                jsonify(
                    {"success": False, "message": "Username cannot contain spaces"}
                ),
                400,
            )

        if data["email"].find("@") == -1:
            return jsonify({"success": False, "message": "Invalid email format"}), 400

        user = Users.query.filter_by(user_id=data["user_id"]).first()
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        user.username = (data["username"],)
        user.email = (data["email"],)
        user.gender = (data["gender"],)
        user.semester = (data["semester"],)
        user.field_of_preference = data["field_of_preference"]

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

        as_invitee = TeamInvitation.query.filter_by(
            invitee_id=current_user.user_id
        ).first()

        team_leader_id = as_invitee.inviter_id if as_invitee else current_user.user_id

        invitations = TeamInvitation.query.filter_by(inviter_id=team_leader_id).all()

        teammate_ids = {team_leader_id}
        for inv in invitations:
            teammate_ids.add(inv.invitee_id)

        teammates = Users.query.filter(Users.user_id.in_(list(teammate_ids))).all()

        return (
            jsonify(
                {"success": True, "teammates": [user.to_dict() for user in teammates]}
            ),
            200,
        )

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
        target_user_id = data.get("user_id")

        if not target_user_id:
            return jsonify({"success": False, "message": "User ID is required"}), 400

        current_user = get_current_user_object()
        if not current_user:
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        invitation = TeamInvitation.query.filter(
            (
                (TeamInvitation.inviter_id == current_user.user_id)
                & (TeamInvitation.invitee_id == target_user_id)
            )
            | (
                (TeamInvitation.invitee_id == current_user.user_id)
                & (TeamInvitation.inviter_id == target_user_id)
            )
        ).first()

        if not invitation:
            return (
                jsonify(
                    {"success": False, "message": "No invitation found with this user"}
                ),
                404,
            )

        db.session.delete(invitation)
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
            return jsonify({"success": False, "message": "Competition not found"}), 500

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
