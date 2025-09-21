"""
Configuration management for HireLens
Handles environment-specific settings and database configuration
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    
    # Application settings
    APP_NAME = "HireLens"
    VERSION = "2.0.0"
    DEBUG = False
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # File upload settings
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}
    UPLOAD_FOLDER = "uploads"
    
    # AI/LLM settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DEFAULT_MODEL = "gpt-3.5-turbo"
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL based on environment"""
        from .db.database import get_database_url
        return get_database_url()
    
    @classmethod
    def is_cloud_environment(cls) -> bool:
        """Check if running in cloud environment"""
        return any([
            os.getenv("STREAMLIT_CLOUD"),
            os.getenv("DYNO"),  # Heroku
            os.getenv("RAILWAY_ENVIRONMENT"),  # Railway
            os.getenv("VERCEL"),  # Vercel
            os.getenv("AWS_LAMBDA_FUNCTION_NAME"),  # AWS Lambda
        ])
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode"""
        return os.getenv("DEVELOPMENT") == "true" or os.getenv("LOCAL_DEV") == "true"

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hirelens_dev.db")

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in production")

class StreamlitCloudConfig(Config):
    """Streamlit Cloud specific configuration"""
    DEBUG = False
    # Force SQLite for Streamlit Cloud
    DATABASE_URL = "sqlite:///./hirelens_cloud.db"
    
    # Streamlit Cloud specific optimizations
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB limit for Streamlit Cloud
    UPLOAD_FOLDER = "/tmp/uploads"  # Use temp directory

def get_config() -> Config:
    """Get configuration based on environment"""
    if Config.is_cloud_environment():
        if os.getenv("STREAMLIT_CLOUD"):
            return StreamlitCloudConfig()
        else:
            return ProductionConfig()
    elif Config.is_development():
        return DevelopmentConfig()
    else:
        return ProductionConfig()

# Global config instance
config = get_config()
