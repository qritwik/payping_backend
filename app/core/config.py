from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/payping"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OTP
    OTP_EXPIRY_MINUTES: int = 10
    OTP_LENGTH: int = 6
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "PayPing API"
    PROJECT_VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

