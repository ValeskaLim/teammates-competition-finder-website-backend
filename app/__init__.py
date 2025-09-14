from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config import Config
from flask_cors import CORS
from flask_mail import Mail
from app.routes import main
from app.extensions import db, mail

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(
        app,
        origins="http://localhost:5173",
        supports_credentials=True,
        methods=["POST", "GET"],
    )

    db.init_app(app)
    migrate = Migrate(app, db)
    mail.init_app(app)
    app.config["SECRET_KEY"] = "secret"

    from app.routes import main

    app.register_blueprint(main)

    with app.app_context():
        # db.create_all()
        pass

    return app


from app import models
