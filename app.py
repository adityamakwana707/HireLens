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

def main():
    """Main entry point - just run the Streamlit app"""
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
