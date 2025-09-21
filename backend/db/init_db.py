"""
Database initialization script for HireLens
"""
from .database import create_tables, drop_tables, engine
from .models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database with all tables"""
    try:
        logger.info("Creating database tables...")
        create_tables()
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def reset_database():
    """Reset the database by dropping and recreating all tables"""
    try:
        logger.info("Dropping existing tables...")
        drop_tables()
        logger.info("Creating fresh tables...")
        create_tables()
        logger.info("Database reset successfully!")
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise

if __name__ == "__main__":
    init_database()
