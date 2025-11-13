import os

from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///suggestions.db")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET", "your-secret-key-here")
    JWT_ALGORITHM: str = "HS256"
    EUREKA_SERVER: str = os.getenv("EUREKA_SERVER", "http://localhost:8761/eureka")
    APP_NAME: str = os.getenv("APP_NAME", "USER-ATTENTION-SERVICE")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()
