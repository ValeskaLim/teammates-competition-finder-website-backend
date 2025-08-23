import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Get the environment (local or docker)
    ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
    
    # Adjust DB_HOST based on environment
    if ENVIRONMENT == "docker":
        DB_HOST = "host.docker.internal"
    else:
        DB_HOST = os.getenv("DB_HOST", "localhost")
    
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


def log_database_uri(self):
    print(f"Database URI: {self.SQLALCHEMY_DATABASE_URI}")
