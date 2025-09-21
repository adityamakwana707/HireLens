"""
Database initialization script for HireLens
Enhanced for dual database strategy
"""
from .database import create_tables, drop_tables, engine, DATABASE_URL, environment
from .models import Base
import logging
import os
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_connection():
    """Check if database connection is working"""
    try:
        with engine.connect() as connection:
            if DATABASE_URL.startswith("sqlite"):
                # Test SQLite connection
                result = connection.execute(text("SELECT 1"))
                logger.info("✅ SQLite database connection successful")
            else:
                # Test PostgreSQL connection
                result = connection.execute(text("SELECT 1"))
                logger.info("✅ PostgreSQL database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def init_database():
    """Initialize the database with all tables"""
    try:
        logger.info(f"🌍 Environment: {environment}")
        logger.info(f"🗄️  Database URL: {DATABASE_URL}")
        
        # Check connection first
        if not check_database_connection():
            raise Exception("Database connection failed")
        
        logger.info("Creating database tables...")
        create_tables()
        logger.info("✅ Database tables created successfully!")
        
        # Log table information
        with engine.connect() as connection:
            if DATABASE_URL.startswith("sqlite"):
                result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = [row[0] for row in result]
            else:
                result = connection.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
                tables = [row[0] for row in result]
            
            logger.info(f"📋 Created tables: {', '.join(tables)}")
        
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        raise

def reset_database():
    """Reset the database by dropping and recreating all tables"""
    try:
        logger.info("⚠️  Dropping existing tables...")
        drop_tables()
        logger.info("Creating fresh tables...")
        create_tables()
        logger.info("✅ Database reset successfully!")
    except Exception as e:
        logger.error(f"❌ Error resetting database: {e}")
        raise

def migrate_sqlite_to_postgresql():
    """Migrate data from SQLite to PostgreSQL (development helper)"""
    if not DATABASE_URL.startswith("postgresql"):
        logger.warning("⚠️  Not a PostgreSQL database, skipping migration")
        return
    
    sqlite_path = "hirelens.db"
    if not os.path.exists(sqlite_path):
        logger.warning(f"⚠️  SQLite database not found at {sqlite_path}")
        return
    
    try:
        from sqlalchemy import create_engine as create_engine_sqlalchemy
        import pandas as pd
        
        # Connect to SQLite
        sqlite_engine = create_engine_sqlalchemy(f"sqlite:///{sqlite_path}")
        
        # Get all tables
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
        
        logger.info(f"📋 Found tables to migrate: {', '.join(tables)}")
        
        # Migrate each table
        for table in tables:
            if table == "sqlite_sequence":  # Skip SQLite system table
                continue
                
            logger.info(f"🔄 Migrating table: {table}")
            df = pd.read_sql_table(table, sqlite_engine)
            df.to_sql(table, engine, if_exists='append', index=False)
            logger.info(f"✅ Migrated {len(df)} rows from {table}")
        
        logger.info("✅ Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_database()
    elif len(sys.argv) > 1 and sys.argv[1] == "migrate":
        migrate_sqlite_to_postgresql()
    else:
        init_database()
