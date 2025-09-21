"""
Final HireLens Enhanced System Startup Script
"""
import subprocess
import sys
import time
import os
from pathlib import Path
import nltk
import spacy

def setup_packages():
    """Setup and verify required NLP packages"""
    print("\n📦 Setting up NLP packages...")
    
    # NLTK Setup
    nltk_packages = ['punkt', 'averaged_perceptron_tagger', 'stopwords']
    for package in nltk_packages:
        try:
            nltk.data.find(f'tokenizers/{package}')
        except LookupError:
            print(f"⏳ Downloading NLTK {package}...")
            nltk.download(package, quiet=True)
    print("✅ NLTK packages verified")
    
    # SpaCy Setup
    try:
        nlp = spacy.load('en_core_web_sm')
        print("✅ SpaCy model verified")
    except OSError:
        print("⏳ Installing SpaCy model...")
        spacy.cli.download('en_core_web_sm')
        print("✅ SpaCy model installed")

def start_final_system():
    """Start the final enhanced HireLens system"""
    print("🚀 Starting HireLens Enhanced System - Final Version")
    print("=" * 70)
    
    # Setup required packages first
    setup_packages()
    
    print("=" * 70)
    print("Backend: http://localhost:8000")
    print("Frontend: http://localhost:8501")
    print("API Docs: http://localhost:8000/docs")
    print("=" * 70)
    print("✨ All Features Available:")
    print("   • Advanced NLP-based JD parsing")
    print("   • Structured field extraction")
    print("   • Skills categorization (must-have vs nice-to-have)")
    print("   • Experience and qualification extraction")
    print("   • Location and job type detection")
    print("   • Compensation and duration parsing")
    print("   • Batch eligibility extraction")
    print("   • Apply button for students")
    print("   • Enhanced error handling")
    print("   • Multiple upload methods:")
    print("     - Single JD upload")
    print("     - Quick upload (sidebar)")
    print("     - Bulk upload (multiple files)")
    print("     - Manual entry")
    print("   • Continue uploading options")
    print("   • Progress tracking")
    print("   • Success/failure metrics")
    print("=" * 70)
    print("🎯 Ready for Hackathon Presentation!")
    print("Press Ctrl+C to stop both services")
    print()
    
    # Start backend in background
    backend_process = subprocess.Popen([
        sys.executable, "enhanced_backend.py"
    ])
    
    # Wait for backend to start
    print("⏳ Starting backend...")
    time.sleep(5)
    
    # Start frontend
    try:
        frontend_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", 
            "run", "enhanced_frontend.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
        
        print("✅ Both services started successfully!")
        print("🌐 Frontend: http://localhost:8501")
        print("🔧 Backend: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("\n🎯 System is ready for Hackathon Presentation!")
        print("Press Ctrl+C to stop...")
        
        # Wait for user to stop
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            backend_process.terminate()
            frontend_process.terminate()
            print("✅ System stopped")
            
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        backend_process.terminate()

if __name__ == "__main__":
    start_final_system()
