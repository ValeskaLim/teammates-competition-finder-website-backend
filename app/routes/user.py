from flask import Blueprint, jsonify, session, request, current_app, make_response
import jwt
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from app.models import Users
from app import db

user_bp = Blueprint('user', __name__, url_prefix="/user")

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

@user_bp.route("/get-all-user", methods=["POST"])
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
    
@user_bp.route("/get-current-user", methods=["POST"])
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

@user_bp.route("/api/user/get-existing-user", methods=["POST"])
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
    
@user_bp.route("/validate-user", methods=["POST"])
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
    
@user_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    res = make_response(jsonify({"message": "Logges out"}))
    res.set_cookie("access_token", "", expires=0, samesite="None", secure=True)

    res.set_cookie("session", "", expires=0, samesite="None", secure=True)
    return res

@user_bp.route("/api/user/submit-register-data", methods=["POST"])
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