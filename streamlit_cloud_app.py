"""
Streamlit Cloud Optimized App for HireLens
This is the main entry point for Streamlit Cloud deployment
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def setup_environment():
    """Setup environment for Streamlit Cloud"""
    # Set environment variables for Streamlit Cloud
    os.environ.setdefault("STREAMLIT_CLOUD", "true")
    
    # Setup NLP packages gracefully
    try:
        import nltk
        nltk_packages = ['punkt', 'averaged_perceptron_tagger', 'stopwords']
        for package in nltk_packages:
            try:
                nltk.data.find(f'tokenizers/{package}')
            except LookupError:
                nltk.download(package, quiet=True)
        logger.info("NLTK packages verified")
    except Exception as e:
        logger.warning(f"NLTK setup failed: {e}")
    
    # Handle SpaCy gracefully (permission issues on Streamlit Cloud)
    try:
        import spacy
        spacy.load('en_core_web_sm')
        logger.info("SpaCy model available")
    except Exception as e:
        logger.warning(f"SpaCy model not available: {e}")
        logger.info("App will continue with limited NLP features")
    
    # Initialize database
    try:
        from backend.db.init_db import init_database
        logger.info("Initializing database...")
        init_database()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Continue anyway - the app will handle database errors gracefully

def main():
    """Main entry point for Streamlit Cloud"""
    logger.info("Starting HireLens on Streamlit Cloud...")
    
    # Setup environment
    setup_environment()
    
    # Import and run the main Streamlit app
    try:
        from frontend.streamlit_app import main as streamlit_main
        streamlit_main()
    except ImportError:
        logger.error("Could not import streamlit app")
        # Fallback to basic Streamlit app
        import streamlit as st
        st.title("HireLens - AI Resume Evaluator")
        st.error("Application failed to load. Please check the logs.")
        st.info("This is a fallback interface. The main application should be accessible.")

if __name__ == "__main__":
    main()
