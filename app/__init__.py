from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    
    db.init_app(app)
    migrate = Migrate(app, db)
    
    from app.routes import main
    app.register_blueprint(main)
    
    with app.app_context():
        # db.create_all()
        pass
    
    return app

from app import models