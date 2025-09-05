from flask import Blueprint
from .user import user_bp
from .team import team_bp
from .competition import competition_bp
from .recommend import recommend_bp

main = Blueprint("main", __name__, url_prefix="/api")

main.register_blueprint(user_bp)
main.register_blueprint(team_bp)
main.register_blueprint(competition_bp)
main.register_blueprint(recommend_bp)