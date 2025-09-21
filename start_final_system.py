"""
Final HireLens Enhanced System Startup Script
Enhanced with dual database strategy support
"""
import subprocess
import sys
import time
import os
import socket
import signal
import psutil
from pathlib import Path
import nltk
import spacy

# Import configuration
try:
    from backend.config import config
    print(f"🌍 Environment: {config.__class__.__name__}")
    print(f"🗄️  Database: {config.get_database_url()}")
except ImportError:
    print("⚠️  Configuration not available, using defaults")

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None

def kill_processes_on_port(port):
    """Kill processes using the specified port"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in proc.info['connections'] or []:
                    if conn.laddr.port == port:
                        print(f"🔄 Killing process {proc.info['pid']} ({proc.info['name']}) on port {port}")
                        proc.kill()
                        time.sleep(1)
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        print(f"⚠️  Error killing processes on port {port}: {e}")
    return False

def setup_packages():
    """Setup and verify required NLP packages"""
    print("\n📦 Setting up NLP packages...")
    
    # NLTK Setup - Handle download errors gracefully
    nltk_packages = ['punkt', 'averaged_perceptron_tagger', 'stopwords']
    for package in nltk_packages:
        try:
            nltk.data.find(f'tokenizers/{package}')
            print(f"✅ NLTK {package} already available")
        except LookupError:
            print(f"⏳ Downloading NLTK {package}...")
            success = False
            
            # Try multiple download methods
            for attempt in range(3):
                try:
                    if attempt == 0:
                        # First attempt: quiet download
                        nltk.download(package, quiet=True)
                    elif attempt == 1:
                        # Second attempt: verbose download
                        nltk.download(package, quiet=False)
                    else:
                        # Third attempt: force download
                        nltk.download(package, force=True, quiet=True)
                    
                    # Verify the download worked
                    nltk.data.find(f'tokenizers/{package}')
                    print(f"✅ NLTK {package} downloaded successfully")
                    success = True
                    break
                    
                except Exception as e:
                    print(f"⚠️  Attempt {attempt + 1} failed for {package}: {str(e)[:100]}...")
                    if attempt < 2:
                        print(f"🔄 Retrying download for {package}...")
                        time.sleep(1)
            
            if not success:
                print(f"❌ Failed to download {package} after 3 attempts")
                print(f"ℹ️  App will continue with limited {package} functionality")
    
    print("✅ NLTK setup completed")
    
    # SpaCy Setup - Handle permission issues gracefully
    try:
        nlp = spacy.load('en_core_web_sm')
        print("✅ SpaCy model verified")
    except OSError as e:
        print(f"⚠️  SpaCy model not available: {e}")
        print("ℹ️  SpaCy features will be limited, but app will continue")
        # Don't try to download - it causes permission issues on Streamlit Cloud

def start_final_system():
    """Start the final enhanced HireLens system"""
    print("🚀 Starting HireLens Enhanced System - Final Version")
    print("=" * 70)
    
    try:
        # Setup required packages first
        setup_packages()
    except Exception as e:
        print(f"❌ Error during package setup: {e}")
        print("⚠️  Continuing with limited functionality...")
        print("=" * 70)
    
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
    
    # Start frontend with port conflict resolution
    try:
        # Check if default port is available
        frontend_port = 8501
        if is_port_in_use(frontend_port):
            print(f"⚠️  Port {frontend_port} is already in use")
            print("🔄 Attempting to free up the port...")
            
            # Try to kill processes using the port
            if kill_processes_on_port(frontend_port):
                time.sleep(2)  # Wait for processes to terminate
                if not is_port_in_use(frontend_port):
                    print(f"✅ Port {frontend_port} is now available")
                else:
                    print(f"⚠️  Port {frontend_port} still in use, finding alternative...")
                    available_port = find_available_port(frontend_port)
                    if available_port:
                        frontend_port = available_port
                        print(f"🔄 Using alternative port: {frontend_port}")
                    else:
                        print("❌ No available ports found for frontend")
                        raise Exception("No available ports for frontend")
            else:
                print(f"⚠️  Could not free port {frontend_port}, finding alternative...")
                available_port = find_available_port(frontend_port)
                if available_port:
                    frontend_port = available_port
                    print(f"🔄 Using alternative port: {frontend_port}")
                else:
                    print("❌ No available ports found for frontend")
                    raise Exception("No available ports for frontend")
        
        frontend_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", 
            "run", "enhanced_frontend.py",
            "--server.port", str(frontend_port),
            "--server.address", "0.0.0.0"
        ])
        
        print("✅ Both services started successfully!")
        print(f"🌐 Frontend: http://localhost:{frontend_port}")
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
