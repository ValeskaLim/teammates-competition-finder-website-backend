import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Get the environment (local or docker)
    ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
    
    # Adjust DB_HOST based on environment
    if ENVIRONMENT == "docker":
        DB_HOST = os.getenv('DB_HOST', 'db')
    else:
        DB_HOST = os.getenv("DB_HOST", "localhost")
    
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")


def log_database_uri(self):
    print(f"Database URI: {self.SQLALCHEMY_DATABASE_URI}")
