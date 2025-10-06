from app.extensions import db
from datetime import datetime, date
from sqlalchemy.dialects.postgresql import JSON


class Users(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    fullname = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(30))
    gender = db.Column(db.String(1), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    major = db.Column(db.String(30), nullable=False)
    field_of_preference = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), nullable=False)
    date_updated = db.Column(db.DateTime(timezone=True), nullable=False)
    token = db.Column(db.String(255), nullable=True)
    token_expiration = db.Column(db.DateTime(timezone=True), nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    profile_picture = db.Column(db.String(255), nullable=True)
    portfolio = db.Column(db.String(255), nullable=True)

    sent_invitations = db.relationship(
        "TeamInvitation",
        foreign_keys="TeamInvitation.inviter_id",
        backref="inviter",
        lazy=True,
    )

    receive_invitations = db.relationship(
        "TeamInvitation",
        foreign_keys="TeamInvitation.invitee_id",
        backref="invitee",
        lazy=True,
    )

    def __repr__(self):
        return f"<Users {self.username}>"

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "fullname": self.fullname,
            "gender": self.gender,
            "semester": self.semester,
            "major": self.major,
            "field_of_preference": self.field_of_preference,
            "portfolio": self.portfolio,
        }


class Competition(db.Model):
    __tablename__ = "competition"

    competition_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False, unique=True)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(db.String(3), nullable=False)
    description = db.Column(db.String(4000), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    min_member = db.Column(db.Integer, nullable=False)
    max_member = db.Column(db.Integer, nullable=False)
    original_url = db.Column(db.Text, nullable=True)
    date_created = db.Column(db.DateTime(timezone=True), nullable=False)
    date_updated = db.Column(db.DateTime(timezone=True), nullable=False)
    poster = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Competition {self.name}>"

    def to_dict(self):
        return {
            "competition_id": self.competition_id,
            "title": self.title,
            "date": self.date.strftime('%Y-%m-%d') if self.date else None,
            "status": self.status,
            "description": self.description,
            "category": self.category,
            "min_member": self.min_member,
            "max_member": self.max_member,
            "original_url": self.original_url if self.original_url else None,
            "poster": self.poster if self.poster else None,
        }


class Teams(db.Model):
    __tablename__ = "teams"

    team_id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.String(200), nullable=False)
    team_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.String(500), nullable=True)
    competition_id = db.Column(db.Integer, db.ForeignKey("competition.competition_id"), nullable=True)
    leader_id = db.Column(db.Integer)
    is_finalized = db.Column(db.Boolean, default=False, nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), nullable=False)
    date_updated = db.Column(db.DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<Teams {self.team_id}>"

    def to_dict(self):
        return {
            "team_id": self.team_id,
            "member_id": self.member_id,
            "team_name": self.team_name,
            "description": self.description,
            "notes": self.notes,
            "competition_id": self.competition_id,
            "leader_id": self.leader_id,
            "is_finalized": self.is_finalized,
            "date_created": (
                self.date_created.isoformat() if self.date_created else None
            ),
            "date_updated": (
                self.date_updated.isoformat() if self.date_updated else None
            )
        }


class TeamInvitation(db.Model):
    __tablename__ = "team_invitation"

    team_invitation_id = db.Column(db.Integer, primary_key=True)
    inviter_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    invitee_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    status = db.Column(db.String(30), nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), nullable=False)
    date_updated = db.Column(db.DateTime(timezone=True))

    def __repr__(self):
        return f"<TeamInvitation {self.team_invitation_id}>"

    def to_dict(self):
        return {
            "team_invitation_id": self.team_invitation_id,
            "inviter_id": self.inviter_id,
            "invitee_id": self.invitee_id,
            "status": self.status,
            "date_created": (
                self.date_created.isoformat() if self.date_created else None
            ),
            "date_updated": (
                self.date_updated.isoformat() if self.date_updated else None
            ),
            "invites": self.inviter.to_dict() if self.inviter else None,
            "invitee": self.invitee.to_dict() if self.invitee else None,
        }
        
class TeamJoin(db.Model):
    __tablename__ = "team_join"

    team_join_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    team_id = db.Column(db.Integer, db.ForeignKey("teams.team_id"))
    status = db.Column(db.String(30), nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), nullable=False)
    date_updated = db.Column(db.DateTime(timezone=True))

    def __repr__(self):
        return f"<TeamJoin {self.team_join_id}>"

    def to_dict(self):
        return {
            "team_join_id": self.team_join_id,
            "user_id": self.user_id,
            "team_id": self.team_id,
            "status": self.status,
            "date_created": (
                self.date_created.isoformat() if self.date_created else None
            ),
            "date_updated": (
                self.date_updated.isoformat() if self.date_updated else None
            )
        }
        
class Skills(db.Model):
    __tablename__ = "skills"

    skill_id = db.Column(db.Integer, primary_key=True)
    skill_code = db.Column(db.String(50), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), nullable=False)
    date_updated = db.Column(db.DateTime(timezone=True), nullable=False)

    def to_dict(self):
        return {
            "skill_code": self.skill_code,
            "skill_name": self.skill_name
        }
