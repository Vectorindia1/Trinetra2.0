#!/usr/bin/env python3
"""
TRINETRA - Full System Startup Script
Starts both the FastAPI backend and serves the React frontend
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """Print startup banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                          TRINETRA                            ║
║                 Dark Web Intelligence System                 ║
║                     Full System Startup                     ║
╚══════════════════════════════════════════════════════════════╝
    """)

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking system requirements...")
    
    # Check if React build exists
    frontend_build = Path("frontend/dist/index.html")
    if not frontend_build.exists():
        print("❌ React frontend not built. Building now...")
        try:
            subprocess.run([
                "npm", "run", "build"
            ], cwd="frontend", check=True, capture_output=True)
            print("✅ React frontend built successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to build React frontend: {e}")
            return False
    else:
        print("✅ React frontend build found")
    
    # Check database
    try:
        from database.models import db_manager
        stats = db_manager.get_threat_statistics()
        print(f"✅ Database connected ({len(stats)} stats available)")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Check API components
    try:
        from api.main import app
        from incident_reporter import LawEnforcementReporter
        print("✅ API components loaded successfully")
    except Exception as e:
        print(f"❌ API components failed to load: {e}")
        return False
    
    return True

def start_api_server():
    """Start the FastAPI server"""
    print("🚀 Starting FastAPI backend server...")
    
    try:
        import uvicorn
        from api.main import app
        
        # Start the server in a separate process
        api_process = subprocess.Popen([
            sys.executable, "-c",
            """
import uvicorn
from api.main import app
uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
            """
        ], cwd=os.getcwd())
        
        print(f"✅ FastAPI server started on PID {api_process.pid}")
        print("📡 API available at: http://localhost:8000")
        print("📚 API docs available at: http://localhost:8000/api/docs")
        
        return api_process
        
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def start_frontend_server():
    """Start a simple HTTP server for the React frontend"""
    print("🌐 Starting React frontend server...")
    
    try:
        # Change to frontend/dist directory and start HTTP server
        frontend_process = subprocess.Popen([
            sys.executable, "-m", "http.server", "3000"
        ], cwd="frontend/dist")
        
        print(f"✅ Frontend server started on PID {frontend_process.pid}")
        print("🎨 Frontend available at: http://localhost:3000")
        
        return frontend_process
        
    except Exception as e:
        print(f"❌ Failed to start frontend server: {e}")
        return None

def main():
    """Main startup function"""
    print_banner()
    
    # Store process references
    processes = []
    
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down TRINETRA system...")
        for process in processes:
            if process and process.poll() is None:
                print(f"   Terminating process {process.pid}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        print("✅ System shutdown complete")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check requirements
    if not check_requirements():
        print("❌ System requirements not met. Exiting.")
        return 1
    
    print("\n" + "="*60)
    print("🚀 STARTING TRINETRA SERVICES")
    print("="*60)
    
    # Start API server
    api_process = start_api_server()
    if api_process:
        processes.append(api_process)
        time.sleep(3)  # Give API time to start
    else:
        print("❌ Failed to start API server. Cannot continue.")
        return 1
    
    # Start frontend server
    frontend_process = start_frontend_server()
    if frontend_process:
        processes.append(frontend_process)
        time.sleep(2)  # Give frontend time to start
    else:
        print("⚠️ Frontend server failed to start, but API is running.")
    
    print("\n" + "="*60)
    print("✅ TRINETRA SYSTEM READY")
    print("="*60)
    print()
    print("🌐 Access Points:")
    print("   • React Dashboard: http://localhost:3000")
    print("   • API Backend:     http://localhost:8000")
    print("   • API Documentation: http://localhost:8000/api/docs")
    print()
    print("🔧 Features Available:")
    print("   • Real-time Dark Web Monitoring")
    print("   • AI-Powered Threat Analysis")
    print("   • Manual Crawler Control")
    print("   • Law Enforcement Incident Reporting")
    print("   • Advanced Link Mapping & Visualization")
    print("   • Automated Alert System")
    print()
    print("Press Ctrl+C to shutdown the system")
    print("="*60)
    
    # Keep the main process alive and monitor child processes
    try:
        while True:
            time.sleep(1)
            
            # Check if any process has died
            for i, process in enumerate(processes):
                if process and process.poll() is not None:
                    print(f"⚠️ Process {process.pid} has stopped unexpectedly")
                    processes[i] = None
            
            # If all processes are dead, exit
            if all(p is None or p.poll() is not None for p in processes):
                print("❌ All services have stopped. Exiting.")
                break
                
    except KeyboardInterrupt:
        pass
    
    # Cleanup
    signal_handler(None, None)
    return 0

if __name__ == "__main__":
    sys.exit(main())
