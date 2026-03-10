import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://insurance:insurance@localhost:5432/insurance_db")
API_KEY: str = os.getenv("API_KEY", "demo-api-key-2025")
