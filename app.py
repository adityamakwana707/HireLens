"""
Main entry point for Streamlit Cloud deployment
This is the simplest possible entry point to avoid conflicts
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set environment for Streamlit Cloud
os.environ.setdefault("STREAMLIT_CLOUD", "true")

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Initialize database and setup environment
def setup_environment():
    """Setup environment for Streamlit Cloud"""
    try:
        # Setup NLP packages gracefully
        import nltk
        nltk_packages = ['punkt', 'averaged_perceptron_tagger', 'stopwords']
        for package in nltk_packages:
            try:
                nltk.data.find(f'tokenizers/{package}')
                logger.info(f"NLTK {package} already available")
            except LookupError:
                try:
                    logger.info(f"Downloading NLTK {package}...")
                    nltk.download(package, quiet=True)
                    logger.info(f"NLTK {package} downloaded successfully")
                except Exception as e:
                    logger.warning(f"Failed to download NLTK {package}: {e}")
                    logger.info(f"App will continue with limited {package} functionality")
        logger.info("NLTK setup completed")
    except Exception as e:
        logger.warning(f"NLTK setup failed: {e}")
        logger.info("App will continue with basic functionality")
    
    # Initialize database
    try:
        from backend.db.init_db import init_database
        logger.info("Initializing database...")
        init_database()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

def main():
    """Main entry point - just run the Streamlit app"""
    # Setup environment first
    setup_environment()
    
    try:
        # Import and run the main Streamlit app
        from frontend.streamlit_app import main as streamlit_main
        streamlit_main()
    except ImportError as e:
        logger.error(f"Could not import streamlit app: {e}")
        # Fallback to basic Streamlit app
        import streamlit as st
        st.title("HireLens - AI Resume Evaluator")
        st.error("Application failed to load. Please check the logs.")
        st.info("This is a fallback interface.")

if __name__ == "__main__":
    main()
