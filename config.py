import os

from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///suggestions.db")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET", "your-secret-key-here")
    JWT_ALGORITHM: str = "HS256"


settings = Settings()
