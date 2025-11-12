import os

from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://admin:admin@localhost:5432/suggestions"
    )


settings = Settings()
