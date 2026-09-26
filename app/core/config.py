import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    APP_NAME: str = "VERDICT AI Backend"
    APP_VERSION: str = "2.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # Security
    SECRET_KEY: str = "verdict-secret-key-hackronix-2.0"
    API_KEY_HEADER: str = "X-VERDICT-API-KEY"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "*"
    ]
    
    # MongoDB Database Configuration (Supports MONGODB_URI and MONGODB_URL)
    MONGODB_URL: str = Field(default=os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
    MONGODB_URI: str = Field(default="")
    MONGODB_DB_NAME: str = Field(default="verdict_db")
    
    # SQL Database (Alternative/Fallback)
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./verdict.db")
    DATABASE_SYNC_URL: str = Field(default="sqlite:///./verdict.db")
    
    # LLM & AI
    GROQ_API_KEY: str = Field(default="")
    GROQ_MODEL: str = "llama3-70b-8192"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    
    # Storage
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "uploads")
    PROCESSED_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "processed")
    
    # Edge Gateway
    EDGE_GATEWAY_URL: str = "http://localhost:8001"
    EDGE_GATEWAY_TOKEN: str = "verdict-edge-token-2026"
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Resolve MongoDB connection string precedence
if settings.MONGODB_URI and not settings.MONGODB_URL.startswith("mongodb+srv"):
    settings.MONGODB_URL = settings.MONGODB_URI

# Ensure storage directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
