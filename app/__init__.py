from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    # Create tables (since you already have the database)
    with app.app_context():
        # This will create tables if they don't exist
        # But since you already have the database, this is optional
        # db.create_all()
        pass
    
    return app

# Import models after db initialization
from app import models