#!/usr/bin/env python3
"""
TRINETRA - Complete System Startup
Starts FastAPI backend, React frontend, and Streamlit dashboard
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

def print_banner():
    """Print startup banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                          TRINETRA                            ║
║                 Dark Web Intelligence System                 ║
║                       Quick Startup                         ║
╚══════════════════════════════════════════════════════════════╝
    """)

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
    
    print("🚀 Starting TRINETRA services...")
    
    # Start API server
    print("📡 Starting FastAPI backend server...")
    api_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "api.main:app", 
        "--host", "0.0.0.0", "--port", "8000"
    ])
    processes.append(api_process)
    print(f"✅ Backend started on PID {api_process.pid}")
    time.sleep(3)  # Give API time to start
    
    # Start frontend server
    print("🌐 Starting React frontend server...")
    frontend_process = subprocess.Popen([
        sys.executable, "-m", "http.server", "3000"
    ], cwd="frontend/dist")
    processes.append(frontend_process)
    print(f"✅ Frontend started on PID {frontend_process.pid}")
    time.sleep(2)
    
    # Start Streamlit dashboard
    print("📊 Starting Streamlit dashboard...")
    streamlit_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "dashboard.py", 
        "--server.port", "8501", "--server.address", "0.0.0.0",
        "--server.headless", "true", "--browser.gatherUsageStats", "false"
    ])
    processes.append(streamlit_process)
    print(f"✅ Streamlit dashboard started on PID {streamlit_process.pid}")
    time.sleep(3)
    
    print("""
============================================================
✅ TRINETRA SYSTEM READY
============================================================

🌐 Access Points:
   • React Dashboard:    http://localhost:3000
   • Streamlit Dashboard: http://localhost:8501
   • API Backend:        http://localhost:8000
   • API Documentation:  http://localhost:8000/api/docs

🔧 Features Available:
   • Real-time Dark Web Monitoring
   • AI-Powered Threat Analysis
   • Manual Crawler Control
   • Law Enforcement Incident Reporting
   • Advanced Link Mapping & Visualization
   • Automated Alert System
   • Enhanced Data Visualization (Streamlit)

Press Ctrl+C to shutdown the system
============================================================
""")
    
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

if __name__ == "__main__":
    main()
