from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config import Config
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, origins="http://localhost:5173", supports_credentials=True, methods=['POST'])
    
    db.init_app(app)
    migrate = Migrate(app, db)
    app.config['SECRET_KEY'] = 'secret'
    
    from app.routes import main
    app.register_blueprint(main)
    
    with app.app_context():
        # db.create_all()
        pass
    
    return app

from app import models