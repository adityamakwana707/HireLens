"""
Simple startup script for HireLens
Handles port conflicts and ensures clean startup
"""
import os
import sys
import time
import subprocess
import signal
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set environment for Streamlit Cloud
os.environ.setdefault("STREAMLIT_CLOUD", "true")

def kill_process_on_port(port):
    """Kill any process running on the specified port"""
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in proc.info['connections'] or []:
                    if conn.laddr.port == port:
                        logger.info(f"Killing process {proc.info['pid']} on port {port}")
                        proc.kill()
                        time.sleep(1)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except ImportError:
        logger.warning("psutil not available, cannot kill existing processes")

def start_backend():
    """Start the backend server"""
    try:
        # Kill any existing backend processes
        kill_process_on_port(8000)
        kill_process_on_port(8001)
        kill_process_on_port(8002)
        
        logger.info("Starting backend server...")
        backend_process = subprocess.Popen([
            sys.executable, "enhanced_backend.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for backend to start
        time.sleep(3)
        
        if backend_process.poll() is None:
            logger.info("✅ Backend started successfully")
            return backend_process
        else:
            logger.error("❌ Backend failed to start")
            return None
            
    except Exception as e:
        logger.error(f"Error starting backend: {e}")
        return None

def start_frontend():
    """Start the Streamlit frontend"""
    try:
        # Kill any existing Streamlit processes
        kill_process_on_port(8501)
        kill_process_on_port(8502)
        kill_process_on_port(8503)
        
        logger.info("Starting Streamlit frontend...")
        frontend_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "frontend/streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "true"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for frontend to start
        time.sleep(3)
        
        if frontend_process.poll() is None:
            logger.info("✅ Frontend started successfully")
            return frontend_process
        else:
            logger.error("❌ Frontend failed to start")
            return None
            
    except Exception as e:
        logger.error(f"Error starting frontend: {e}")
        return None

def main():
    """Main startup function"""
    logger.info("🚀 Starting HireLens Application")
    logger.info("=" * 50)
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        logger.error("Failed to start backend, exiting")
        return
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        logger.error("Failed to start frontend, exiting")
        backend_process.terminate()
        return
    
    logger.info("🎉 Both services started successfully!")
    logger.info("🌐 Frontend: http://localhost:8501")
    logger.info("🔧 Backend: http://localhost:8000")
    logger.info("Press Ctrl+C to stop...")
    
    try:
        # Wait for user to stop
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down...")
        backend_process.terminate()
        frontend_process.terminate()
        logger.info("✅ Application stopped")

if __name__ == "__main__":
    main()
