from app import db
from datetime import datetime, date
from sqlalchemy.dialects.postgresql import JSON


class Users(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    fullname = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(30))
    gender = db.Column(db.String(1), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    major = db.Column(db.String(30), nullable=False)
    field_of_preference = db.Column(db.String(500), nullable=False)

    user_competitions = db.relationship("UserCompetition", backref="users", lazy=True)

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
        }


class Competition(db.Model):
    __tablename__ = "competition"

    competition_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False, unique=True)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(3), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    slot = db.Column(db.Integer, nullable=False)

    user_competition = db.relationship(
        "UserCompetition", backref="competition", lazy=True
    )

    def __repr__(self):
        return f"<Competition {self.name}>"

    def to_string(self):
        return {
            "competition_id": self.competition_id,
            "title": self.title,
            "date": self.date.isoformat() if self.date else None,
            "status": self.status,
            "description": self.description,
            "type": self.type,
            "slot": self.slot,
        }


class UserCompetition(db.Model):
    __tablename__ = "user_competition"

    user_competition_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    competition_id = db.Column(db.Integer, db.ForeignKey("competition.competition_id"))
    created_by = db.Column(db.String(100))
    date_created = db.Column(db.DateTime(timezone=False), nullable=False)
    date_updated = db.Column(db.DateTime(timezone=False), nullable=False)

    def __repr__(self):
        return f"<UserCompetition {self.user_competition_id}>"

    def to_dict(self):
        return {
            "user_competition_id": self.user_competition_id,
            "user_id": self.user_id,
            "competition_id": self.competition_id,
            "created_by": self.created_by,
            "date_created": (
                self.date_created.isoformat() if self.date_created else None
            ),
            "date_updated": (
                self.date_updated.isoformat() if self.date_updated else None
            ),
            "users": self.user.to_dict() if self.user else None,
            "competition": self.competition.to_dict() if self.competition else None,
        }


class TeamInvitation(db.Model):
    __tablename__ = "team_invitation"

    team_invitation_id = db.Column(db.Integer, primary_key=True)
    inviter_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    invitee_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    status = db.Column(db.String(30), nullable=False)
    date_created = db.Column(db.DateTime(timezone=False), nullable=False)
    date_updated = db.Column(db.DateTime(timezone=False))

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
            "inviter": self.inviter.to_dict() if self.inviter else None,
            "invitee": self.invitee.to_dict() if self.invitee else None,
        }
