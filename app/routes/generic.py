from flask import session, request
from app.models import Users, Teams
from app.extensions import db, mail
import jwt
import os
import pytz
from datetime import datetime

UPLOAD_FOLDER = "/app/uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def now_jakarta():
    return datetime.now(pytz.timezone('Asia/Jakarta'))

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

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def check_is_already_have_team(user_id):
    str_user_id = str(user_id)
    query = Teams.query

    is_have_team = query.filter(
        Teams.member_id.ilike(f"%{str_user_id}%")
    ).first()

    return is_have_team is not None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS