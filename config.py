import os

from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///suggestions.db")
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET",
        "d3ee61e796a04895924719559f19a19de2e31d4c330208d8c410c2d63c89de9b5aadc298404a843d521569e812c599bda47b65d4c7fce5a8ded21f24d8df59dc",
    )
    JWT_ALGORITHM: str = "HS256"
    EUREKA_SERVER: str = os.getenv("EUREKA_SERVER", "http://localhost:8761/eureka")
    APP_NAME: str = os.getenv("APP_NAME", "USER-ATTENTION-SERVICE")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()
