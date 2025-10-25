from flask import Blueprint, jsonify, session, request, current_app, make_response
import jwt
import re
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from datetime import datetime, timedelta
from app.models import Skills, Users, Teams, TeamInvitation, Competition
from app.extensions import db
from flask_mail import Message
import threading
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from app.routes.generic import send_async_email, check_is_already_have_team, now_jakarta
from app.utils.response import success_response, error_response

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
    
@user_bp.route("/get-current-user", methods=["POST"])
def get_current_user():

    user = get_current_user_object()
    if not user:
        return jsonify({"user": None}), 200

    return jsonify({
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
            "is_verified": user.is_verified,
            "portfolio": user.portfolio,
        }
    }), 200

@user_bp.route("/get-existing-user", methods=["POST"])
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
        
@user_bp.route("/get-user-by-id", methods=["POST"])
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
        
@user_bp.route("/get-invites-user", methods=["POST"])
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
        
@user_bp.route("/get-invitees-user", methods=["POST"])
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
        
@user_bp.route("/get-list-skillset", methods=["POST"])
def get_list_skillset():
    try:
        query = Skills.query
        skillset = query.all()

        return success_response(data=[skill.to_dict() for skill in skillset], status=200)

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error fetching skillset: {str(e)}"}),
            500,
        )

@user_bp.route("/login", methods=["POST"])
def login():
    try:
        req = request.get_json()

        is_user_exist = Users.query.filter(Users.email == req["email"]).first()
        
        # Double checking in case old password format is used
        if is_user_exist is None:
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401
            
        is_credential_valid = (
            check_password_hash(is_user_exist.password, req["password"])
            if is_user_exist.password.startswith("pbkdf2:sha256:")
            else is_user_exist.password == req["password"]
        )\
            
        if not is_credential_valid:
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401
            
        if not is_user_exist.is_verified:
            return jsonify({
                "success": False,
                "message": "Please verify your email before logging in"
            }), 401

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
    
@user_bp.route("/get-all-teammates", methods=["POST"])
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
            or_(
                Teams.member_id == str(current_user.user_id),
                Teams.member_id.ilike(f"{current_user.user_id},%"),
                Teams.member_id.ilike(f"%,{current_user.user_id},%"), 
                Teams.member_id.ilike(f"%,{current_user.user_id}")
            )
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
        
@user_bp.route("/invite-user", methods=["POST"])
def invite_user():
    try:
        req = request.get_json()
        current_user = get_current_user_object()

        new_invitation = TeamInvitation(
            inviter_id = current_user.user_id,
            invitee_id = req["user_id"],
            status = "P",
            date_created = now_jakarta(),
            date_updated = now_jakarta()
        )
        
        db.session.add(new_invitation)
        db.session.commit()

        # Notify invited user by email
        invitee = Users.query.filter(Users.user_id == req["user_id"]).first()

        if invitee and invitee.email:
            try:
                msg = Message(
                    subject = "You have been invited!",
                    recipients = [invitee.email],
                    body = (
                        f"Hello {invitee.username},\n\n"
                        f"{current_user.username} has invited you to join their team.\n\n"
                        f"Please log in to accept or decline the invitation.\n\n"
                        f"Best regards,\nYour Team"
                    ),
                    html=(
                        f"<p>Hello {invitee.username},</p>"
                        f"<p><b>{current_user.username}</b> has invited you to join their team.</p>"
                        f"<p>Please log in to accept or decline the invitation.</p>"
                        f"<p>Best regards,<br><b>Your Team</b></p>"
                    )
                )

                threading.Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

            except Exception as mail_error:
                print("Email not send!")
        
        return jsonify({
            "success": True,
            "message": "User invited successfully"
        }), 200
        
    except Exception as e:
        return (
            jsonify({
                "success": False, 
                "message": f"Error fetching users: {str(e)}"
            }), 500
        )
        
@user_bp.route("/remove-user-invitation", methods=["POST"])
def remove_user_invitation():
    try:
        req = request.get_json()
        query = TeamInvitation.query

        invitatee_to_remove = query.filter(
            TeamInvitation.invitee_id == req["user_id"]
        ).first()

        if invitatee_to_remove is None:
            return jsonify({
                "success": False,
                "message": "Invites not found"
            }), 404
        
        if invitatee_to_remove == "A":
            return jsonify({
                "success": False,
                "message": "Cannot remove invites with status Active"
            }), 500
        
        db.session.delete(invitatee_to_remove)
        db.session.commit()

        return jsonify({
                "success": True,
                "messages": "Invitee successfully removed"
            }), 200

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error removing user: {str(e)}"}),
            500,
        )
        
@user_bp.route("/accept-invites", methods=["POST"])
def accept_invites():
    try:
        current_user = get_current_user_object()
        req = request.get_json()
        query = TeamInvitation.query

        team_invitation = query.filter(
            TeamInvitation.inviter_id == req["user_id"], TeamInvitation.status == "P", TeamInvitation.invitee_id == current_user.user_id
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

        get_inviter_team = Teams.query.filter(
            Teams.member_id.ilike(f"%{req['user_id']}%")
        ).first()

        if get_inviter_team is None:
            return jsonify({
                "success": False,
                "message": "Team not found"
            }), 404
            
        if get_inviter_team.is_finalized:
            return error_response("Cannot accept invitation. Team is already finalized.", status=500)
        
        inviter_team_competition = Competition.query.filter(
            Competition.competition_id == get_inviter_team.competition_id
        ).first()
        
        if inviter_team_competition.max_member == member_length:
            return error_response("Cannot accept invitation. Team has reached maximum member limit.", status=500)

        member_length = 0
        members = []
        for member_id in get_inviter_team.member_id.split(","):
            if member_id.strip().isdigit():
                members.append(int(member_id))
                member_length += 1
        
        get_inviter_team.member_id += f",{current_user.user_id}"
        
        team_invitation.status = "A"
        team_invitation.date_updated = now_jakarta()

        db.session.commit()

        # Notify inviter user by email
        inviter = Users.query.filter(Users.user_id == req["user_id"]).first()

        if inviter and inviter.email:
            try:
                msg = Message(
                    subject = "Invitation Accepted!",
                    recipients = [inviter.email],
                    body = (
                        f"Hello {inviter.username},\n\n"
                        f"Good news! {current_user.username} has accepted your invitation to join your team.\n\n"
                        f"Check Teammates List to check your team member.\n\n"
                        f"Best regards,\nYour Team"
                    ),
                    html=(
                        f"<p>Hello {inviter.username},</p>"
                        f"<p>Good news! <b>{current_user.username}</b> has accepted your invitation to join your team.</p>"
                        f"<p>Check <b>Teammates List</b> to check your team member.</p>"
                        f"<p>Best regards,<br><b>Your Team</b></p>"
                    )
                )

                threading.Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

            except Exception as mail_error:
                print("Email not send!")

        return jsonify({
            "success": True,
            "messages": "Invites successfully accepted"
        }), 200

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error fetching users: {str(e)}"}),
            500,
        )
        
@user_bp.route("/reject-invites", methods=["POST"])
def reject_invites():
    try:
        req = request.get_json()
        current_user = get_current_user_object()
        query = TeamInvitation.query

        invitation_to_remove = query.filter(
            TeamInvitation.inviter_id == req["user_id"], TeamInvitation.status == "P", TeamInvitation.invitee_id == current_user.user_id
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
        
        invitation_to_remove.status = "R"
        invitation_to_remove.date_updated = now_jakarta()
        db.session.commit()

        # Notify inviter user by email
        inviter = Users.query.filter(Users.user_id == req["user_id"]).first()

        if inviter and inviter.email:
            try:
                msg = Message(
                    subject = "Invitation Rejected",
                    recipients = [inviter.email],
                    body = (
                        f"Hello {inviter.username},\n\n"
                        f"We’d like to let you know that {current_user.username} has declined your invitation to join the team.\n\n"
                        f"You can invite other members from the Recommendation List.\n\n"
                        f"Best regards,\nYour Team"
                    ),
                    html=(
                        f"<p>Hello {inviter.username},</p>"
                        f"<p>We’d like to let you know that <b>{current_user.username}</b> has declined your invitation to join the team.</p>"
                        f"<p>You can invite other members from the <b>Recommendation</b> List.</p>"
                        f"<p>Best regards,<br><b>Your Team</b></p>"
                    )
                )

                threading.Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

            except Exception as mail_error:
                print("Email not send!")

        return jsonify({
                "success": True,
                "messages": "Invites successfully removed"
            }), 200

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"Error fetching users: {str(e)}"}),
            500,
        )
    
@user_bp.route("/check-is-have-team", methods=["POST"])
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
    
@user_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    res = make_response(jsonify({"message": "Logges out"}))
    res.set_cookie("access_token", "", expires=0, samesite="None", secure=True)

    res.set_cookie("session", "", expires=0, samesite="None", secure=True)
    return res

@user_bp.route("/submit-register-data", methods=["POST"])
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

        hashed_password = generate_password_hash(data["password"], method='pbkdf2:sha256', salt_length=16)
        
        verification_token = secrets.token_urlsafe(16)

        new_user = Users(
            username=data["username"],
            password=hashed_password,
            email=data["email"],
            role="normal",
            fullname=data["fullname"],
            gender=data["gender"],
            semester=data["semester"],
            major="Computer Science",
            field_of_preference=data["field_of_preference"],
            date_created=now_jakarta(),
            date_updated=now_jakarta(),
            token=verification_token,
            token_expiration=now_jakarta() + timedelta(hours=1),
            is_verified=False,
        )

        db.session.add(new_user)
        db.session.commit()
        
        # Send verification email
        verification_link = f"http://localhost:5173/verify-email/{verification_token}"
        try:
            msg = Message(
                subject="Verify Your Email",
                recipients=[data["email"]],
                body=(
                    f"Hello {new_user.username},\n\n"
                    f"Please verify your email by clicking the link below:\n"
                    f"{verification_link}\n\n"
                    f"This link will expire in 1 hour.\n\n"
                    f"Best regards,\nSunib HALL"
                ),
                html=(
                    f"<p>Hello {new_user.username},</p>"
                    f"<p>Please verify your email by clicking the link below:</p>"
                    f"<p><a href='{verification_link}'>{verification_link}</a></p>"
                    f"<p>This link will expire in 1 hour.</p>"
                    f"<p>Best regards,<br><b>Sunib HALL</b></p>"
                ),
            )
            
            threading.Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
            
        except Exception as mail_error:
            print(f"Verification email not sent to {new_user.email}: {mail_error}")

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Email verification sent. Please check your email.",
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
        
@user_bp.route("/verify-email", methods=["POST"])
def verify_email():
    try:
        req = request.get_json()
        token = req.get("token")
        user = Users.query.filter(Users.token == token).first()
        
        print(user, flush=True)
        
        if user is None:
            return error_response("Invalid token", status=500)
            
        if user.token_expiration < now_jakarta():
            db.session.delete(user)
            db.session.commit()
            
            return error_response("Token expired and has been invalidated", status=500)
            
        user.is_verified = True
        user.token = None
        user.token_expiration = None
        user.date_updated = now_jakarta()
        
        db.session.commit()
        
        return success_response("Email successfully verified", status=200)
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Error verifying email: {str(e)}", status=500)
        
@user_bp.route("/edit-user", methods=["POST"])
def edit_user():
    try:
        data = request.get_json()
        print(data, flush=True)
        query = Users.query

        required_fields = ["username", "email", "field_of_preference", "major"]
        
        link_regex = re.compile(r'^(https?:\/\/)?(www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}.*$')
        
        for field in required_fields:
            if field not in data or data[field] == "":
                return error_response(f"Missing or empty required field: {field[0].upper() + field[1:]}", status=400)

        if " " in data["username"]:
            return error_response("Username cannot contain spaces", status=400)

        if data["email"].find("@") == -1:
            return error_response("Invalid email format", status=400)
        
        if data["major"] == " ":
            return error_response("Major cannot be empty", status=400)

        if data["portfolio"] and not re.match(link_regex, data["portfolio"]):
            return error_response("Invalid portfolio link format", status=400)

        user = query.filter_by(user_id=data["user_id"]).first()
        if not user:
            return error_response("User not found", status=404)

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
            return error_response("Username or email already exist", status=500)

        user.username = data["username"],
        user.email = data["email"],
        user.gender = data["gender"],
        user.semester = data["semester"],
        user.field_of_preference = data["field_of_preference"]
        user.major = data["major"]
        user.portfolio = data.get("portfolio", None)
        user.date_updated=now_jakarta()

        db.session.commit()

        return success_response("Edit user successfully", status=200)

    except Exception as e:
        return error_response(f"Error editing user: {str(e)}", status=500)
        
@user_bp.route("/change-password", methods=["POST"])
def change_password():
    try:
        data = request.get_json()
        current_user = get_current_user_object()
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        
        if len(new_password) < 4:
            return error_response("New password must be at least 4 characters long", status=406)
        
        if old_password is None or new_password is None:
            return error_response("Password cannot be null", status=500)

        if not check_password_hash(current_user.password, old_password):
            return error_response("Old password is incorrect", status=401)

        new_hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=16)

        current_user.password = new_hashed_password
        current_user.date_updated = now_jakarta()
        
        db.session.commit()

        return success_response("Password changed successfully", status=200)

    except Exception as e:
        return error_response(f"Error changing password: {str(e)}", status=500)
    
@user_bp.route("/reset-password", methods=["POST"])
def reset_password():
    try:
        data = request.get_json()
        email = data.get("email")
        
        if email is None:
            return error_response("Email cannot be null", status=500)
        
        user = Users.query.filter(Users.email == email).first()
        if user is None:
            return success_response("Password reset email sent", status=200)

        reset_token = secrets.token_urlsafe(16)
        
        user.token = reset_token
        user.token_expiration = now_jakarta() + timedelta(hours=1)
        user.date_updated = now_jakarta()

        db.session.commit()

        reset_link = f"http://localhost:5173/reset-password-final/{reset_token}"
        try:
            msg = Message(
                subject="Reset Your Password",
                recipients=[data["email"]],
                body=(
                    f"Hello {user.username},\n\n"
                    f"You just requested a password reset\n"
                    f"Please reset your password by clicking the link below:\n"
                    f"{reset_link}\n\n"
                    f"This link will expire in 1 hour.\n\n"
                    f"Best regards,\nSunib HALL"
                ),
                html=(
                    f"<p>Hello {user.username},</p>"
                    f"<p>You just requested a password reset</p>"
                    f"<p>Please reset your password by clicking the link below:</p>"
                    f"<p><a href='{reset_link}'>{reset_link}</a></p>"
                    f"<p>This link will expire in 1 hour.</p>"
                    f"<p>Best regards,<br><b>Sunib HALL</b></p>"
                )
            )
            
            threading.Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
            
        except Exception as mail_error:
            print(f"Verification email not sent to {user.email}: {mail_error}")

        return success_response("Password reset email sent", status=200)

    except Exception as e:
        return error_response(f"Error resetting password: {str(e)}", status=500)
    
@user_bp.route("/validate-token", methods=["POST"])
def validate_token():
    try:
        data = request.get_json()
        token = data.get("token")
        user = Users.query.filter(Users.token == token).first()
        
        if user is None:
            return error_response("Invalid token", status=500)
            
        if user.token_expiration < now_jakarta():
            # user.token = None
            # user.token_expiration = None
            # db.session.commit()
            return error_response("Token expired", status=500)
        
        return success_response("Token is valid", status=200)
        
    except Exception as e:
        return error_response(f"Error validating token: {str(e)}", status=500)
    
@user_bp.route("/reset-password-final", methods=["POST"])
def reset_password_final():
    try:
        data = request.get_json()
        token = data.get("token")
        new_password = data.get("new_password")
        
        if len(new_password) < 4:
            return error_response("New password must be at least 4 characters long", status=406)
        
        user = Users.query.filter(Users.token == token).first()
        
        if user is None:
            return error_response("Invalid token", status=500)
            
        if user.token_expiration < now_jakarta():
            return error_response("Token expired", status=500)
        
        new_hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=16)

        user.password = new_hashed_password
        user.token = None
        user.token_expiration = None
        user.date_updated = now_jakarta()
        
        db.session.commit()
        
        return success_response("Password has been reset successfully", status=200)
    
    except Exception as e:
        return error_response(f"Error resetting password: {str(e)}", status=500)