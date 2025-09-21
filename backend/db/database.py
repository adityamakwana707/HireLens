"""
Database configuration and session management for HireLens
Dual database strategy: PostgreSQL for development, SQLite for production/Streamlit Cloud
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import platform
from dotenv import load_dotenv

load_dotenv()

def detect_environment():
    """
    Detect the current environment and determine database strategy
    """
    # Check for Streamlit Cloud environment
    if os.getenv("STREAMLIT_CLOUD"):
        return "streamlit_cloud"
    
    # Check for Heroku environment
    if os.getenv("DYNO"):
        return "heroku"
    
    # Check for Railway environment
    if os.getenv("RAILWAY_ENVIRONMENT"):
        return "railway"
    
    # Check for local development
    if os.getenv("DEVELOPMENT") == "true" or os.getenv("LOCAL_DEV") == "true":
        return "development"
    
    # Default to production if no specific indicators
    return "production"

def get_database_url():
    """
    Get the appropriate database URL based on environment
    """
    environment = detect_environment()
    
    # For Streamlit Cloud and other cloud platforms, use SQLite
    if environment in ["streamlit_cloud", "heroku", "railway"]:
        # Use a persistent SQLite database in the app directory
        db_path = os.path.join(os.getcwd(), "hirelens_cloud.db")
        return f"sqlite:///{db_path}"
    
    # For development, check if PostgreSQL is available
    if environment == "development":
        postgres_url = os.getenv("DATABASE_URL")
        if postgres_url and postgres_url.startswith("postgresql"):
            print("🐘 Using PostgreSQL for development")
            return postgres_url
        else:
            print("📁 Using SQLite for development (PostgreSQL not configured)")
            return "sqlite:///./hirelens.db"
    
    # For production, prefer PostgreSQL but fallback to SQLite
    postgres_url = os.getenv("DATABASE_URL")
    if postgres_url and postgres_url.startswith("postgresql"):
        print("🐘 Using PostgreSQL for production")
        return postgres_url
    else:
        print("📁 Using SQLite for production (PostgreSQL not available)")
        return "sqlite:///./hirelens_prod.db"

# Get the appropriate database URL
DATABASE_URL = get_database_url()
environment = detect_environment()

print(f"🌍 Environment: {environment}")
print(f"🗄️  Database: {DATABASE_URL}")

# Create engine based on database type
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration - optimized for cloud deployment
    engine = create_engine(
        DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
        # SQLite-specific optimizations
        pool_pre_ping=True,
        pool_recycle=3600
    )
    print("✅ SQLite engine configured")
else:
    # PostgreSQL configuration
    try:
        engine = create_engine(
            DATABASE_URL,
            poolclass=StaticPool,
            connect_args={
                "sslmode": "require" if environment == "production" else "prefer",
                "options": "-c timezone=utc"
            },
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        print("✅ PostgreSQL engine configured")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("🔄 Falling back to SQLite...")
        DATABASE_URL = "sqlite:///./hirelens_fallback.db"
        engine = create_engine(
            DATABASE_URL,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=False
        )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db():
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Create all tables in the database
    """
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """
    Drop all tables in the database
    """
    Base.metadata.drop_all(bind=engine)
