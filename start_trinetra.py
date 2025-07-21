#!/usr/bin/env python3

import os
import sys
import subprocess
import signal
import time
import threading
from pathlib import Path

class TrinetraLauncher:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = True
        
    def print_header(self):
        print("🕵️  Starting TRINETRA - Dark Web Intelligence System...")
        print("=" * 50)
    
    def print_success(self):
        print("\033[92m" + "=" * 50)
        print("🕵️  TRINETRA is now running!")
        print("=" * 50)
        print("🌐 Frontend: http://localhost:3000")
        print("🔌 Backend:  http://localhost:8000") 
        print("📊 API Docs: http://localhost:8000/docs")
        print("=" * 50)
        print("Press Ctrl+C to stop both servers" + "\033[0m")
    
    def cleanup(self):
        print("\n\033[91m🛑 Shutting down TRINETRA...\033[0m")
        print("Stopping all processes...")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                print("✓ Backend API stopped")
            except:
                self.backend_process.kill()
                print("✓ Backend API force stopped")
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                print("✓ Frontend React server stopped")
            except:
                self.frontend_process.kill()
                print("✓ Frontend React server force stopped")
        
        print("🕵️  TRINETRA shutdown complete.")
        self.running = False
    
    def signal_handler(self, signum, frame):
        self.cleanup()
        sys.exit(0)
    
    def start_backend(self):
        print("\033[94m🚀 Starting FastAPI Backend Server...\033[0m")
        try:
            # Change to project directory
            os.chdir("/home/vector/darknet_crawler")
            
            # Start FastAPI server
            self.backend_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", "api.main:app",
                "--host", "0.0.0.0", "--port", "8000", "--reload"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            return True
        except Exception as e:
            print(f"\033[91m❌ Failed to start backend: {e}\033[0m")
            return False
    
    def start_frontend(self):
        print("\033[94m⚛️  Starting React Frontend Server...\033[0m")
        try:
            # Change to frontend directory
            frontend_dir = "/home/vector/darknet_crawler/frontend"
            
            # Start React development server
            self.frontend_process = subprocess.Popen([
                "npm", "start"
            ], cwd=frontend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            return True
        except Exception as e:
            print(f"\033[91m❌ Failed to start frontend: {e}\033[0m")
            return False
    
    def check_requirements(self):
        """Check if required files and directories exist"""
        project_dir = Path("/home/vector/darknet_crawler")
        
        if not (project_dir / "api" / "main.py").exists():
            print("\033[91m❌ Error: api/main.py not found\033[0m")
            return False
            
        if not (project_dir / "frontend").is_dir():
            print("\033[91m❌ Error: frontend/ directory not found\033[0m")
            return False
            
        if not (project_dir / "frontend" / "package.json").exists():
            print("\033[91m❌ Error: frontend/package.json not found\033[0m")
            return False
            
        return True
    
    def monitor_processes(self):
        """Monitor both processes and restart if needed"""
        while self.running:
            time.sleep(2)
            
            # Check backend
            if self.backend_process and self.backend_process.poll() is not None:
                print("\033[91m⚠️  Backend process died, attempting restart...\033[0m")
                self.start_backend()
            
            # Check frontend
            if self.frontend_process and self.frontend_process.poll() is not None:
                print("\033[91m⚠️  Frontend process died, attempting restart...\033[0m")
                self.start_frontend()
    
    def run(self):
        """Main execution function"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.print_header()
        
        # Check requirements
        if not self.check_requirements():
            print("Please run this script from the darknet_crawler directory")
            sys.exit(1)
        
        # Start backend
        if not self.start_backend():
            sys.exit(1)
        
        # Wait for backend to start
        time.sleep(3)
        
        # Start frontend
        if not self.start_frontend():
            self.cleanup()
            sys.exit(1)
        
        # Wait for frontend to start
        time.sleep(5)
        
        self.print_success()
        
        # Start monitoring in a separate thread
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.cleanup()

if __name__ == "__main__":
    launcher = TrinetraLauncher()
    launcher.run()
