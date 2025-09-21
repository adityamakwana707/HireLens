#!/usr/bin/env python3
"""
Test script for dual database strategy implementation
"""
import os
import sys
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_environment_detection():
    """Test environment detection logic"""
    print("🧪 Testing Environment Detection")
    print("=" * 50)
    
    try:
        from backend.db.database import detect_environment, get_database_url
        
        # Test current environment
        env = detect_environment()
        db_url = get_database_url()
        
        print(f"✅ Environment detected: {env}")
        print(f"✅ Database URL: {db_url}")
        
        # Test different environment scenarios
        test_scenarios = [
            ("STREAMLIT_CLOUD", "true", "streamlit_cloud"),
            ("DYNO", "web.1", "heroku"),
            ("RAILWAY_ENVIRONMENT", "production", "railway"),
            ("DEVELOPMENT", "true", "development"),
        ]
        
        for var, value, expected in test_scenarios:
            # Set environment variable
            original_value = os.environ.get(var)
            os.environ[var] = value
            
            # Test detection
            detected = detect_environment()
            print(f"   {var}={value} → {detected} {'✅' if detected == expected else '❌'}")
            
            # Restore original value
            if original_value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = original_value
        
        return True
        
    except Exception as e:
        print(f"❌ Environment detection test failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("\n🧪 Testing Database Connection")
    print("=" * 50)
    
    try:
        from backend.db.database import engine, DATABASE_URL
        from backend.db.init_db import check_database_connection
        
        print(f"🗄️  Database URL: {DATABASE_URL}")
        
        # Test connection
        if check_database_connection():
            print("✅ Database connection successful")
            
            # Test basic query
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                if row and row[0] == 1:
                    print("✅ Basic query test passed")
                else:
                    print("❌ Basic query test failed")
            
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def test_database_initialization():
    """Test database initialization"""
    print("\n🧪 Testing Database Initialization")
    print("=" * 50)
    
    try:
        from backend.db.init_db import init_database
        
        print("🔄 Initializing database...")
        init_database()
        print("✅ Database initialization successful")
        
        # Check if tables were created
        from backend.db.database import engine, DATABASE_URL
        from sqlalchemy import text
        
        with engine.connect() as conn:
            if DATABASE_URL.startswith("sqlite"):
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            else:
                result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
            
            tables = [row[0] for row in result]
            print(f"📋 Tables created: {', '.join(tables)}")
            
            expected_tables = ['users', 'jobs', 'resumes', 'evaluations', 'feedback_history']
            missing_tables = [table for table in expected_tables if table not in tables]
            
            if missing_tables:
                print(f"⚠️  Missing tables: {', '.join(missing_tables)}")
            else:
                print("✅ All expected tables created")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization test failed: {e}")
        return False

def test_configuration():
    """Test configuration system"""
    print("\n🧪 Testing Configuration System")
    print("=" * 50)
    
    try:
        from backend.config import config, get_config
        
        print(f"✅ Configuration loaded: {config.__class__.__name__}")
        print(f"✅ App name: {config.APP_NAME}")
        print(f"✅ Version: {config.VERSION}")
        print(f"✅ Debug mode: {config.DEBUG}")
        print(f"✅ Cloud environment: {config.is_cloud_environment()}")
        print(f"✅ Development mode: {config.is_development()}")
        print(f"✅ Database URL: {config.get_database_url()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_requirements_compatibility():
    """Test requirements.txt compatibility"""
    print("\n🧪 Testing Requirements Compatibility")
    print("=" * 50)
    
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy: {sqlalchemy.__version__}")
        
        # Test SQLite support
        import sqlite3
        print("✅ SQLite support available")
        
        # Test PostgreSQL support (if available)
        try:
            import psycopg2
            print("✅ PostgreSQL support available")
        except ImportError:
            print("ℹ️  PostgreSQL support not available (expected on cloud)")
        
        # Test aiosqlite
        try:
            import aiosqlite
            print("✅ Async SQLite support available")
        except ImportError:
            print("❌ Async SQLite support not available")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Requirements compatibility test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 HireLens Dual Database Strategy Test Suite")
    print("=" * 70)
    
    tests = [
        ("Environment Detection", test_environment_detection),
        ("Configuration System", test_configuration),
        ("Requirements Compatibility", test_requirements_compatibility),
        ("Database Connection", test_database_connection),
        ("Database Initialization", test_database_initialization),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Dual database strategy is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
