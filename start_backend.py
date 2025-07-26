#!/usr/bin/env python3
"""
TRINETRA - Backend Only Startup
Starts only the FastAPI backend to reduce resource usage
"""

import os
import sys
import subprocess
import signal
import time

def print_banner():
    """Print startup banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                          TRINETRA                            ║
║                 Dark Web Intelligence System                 ║
║                       Backend Only                           ║
╚══════════════════════════════════════════════════════════════╝
    """)

def main():
    """Main startup function"""
    print_banner()
    
    # Store process reference
    api_process = None
    
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down TRINETRA backend...")
        if api_process and api_process.poll() is None:
            print(f"   Terminating backend process {api_process.pid}")
            api_process.terminate()
            try:
                api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api_process.kill()
        print("✅ Backend shutdown complete")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Starting TRINETRA backend...")
    
    # Start API server
    print("📡 Starting FastAPI backend server...")
    api_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "api.main:app", 
        "--host", "0.0.0.0", "--port", "8000",
        "--log-level", "warning"  # Reduce log verbosity
    ])
    print(f"✅ Backend started on PID {api_process.pid}")
    
    print("""
============================================================
✅ TRINETRA BACKEND READY
============================================================

🌐 Access Points:
   • API Backend:     http://localhost:8000
   • API Documentation: http://localhost:8000/api/docs

📝 To start frontend separately:
   cd frontend && python3 -m http.server 3000 --directory dist

Press Ctrl+C to shutdown the backend
============================================================
""")
    
    # Keep the main process alive and monitor backend
    try:
        while True:
            time.sleep(5)
            
            # Check if backend process has died
            if api_process.poll() is not None:
                print("❌ Backend process has stopped unexpectedly. Exiting.")
                break
                
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
