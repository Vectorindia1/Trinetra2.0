#!/usr/bin/env python3

import subprocess
import sys
import os
import signal
import time
import socket

def is_port_in_use(port):
    """Check if a port is currently in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    """Kill any process using the specified port"""
    try:
        # Find processes using the port
        result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    subprocess.run(['kill', '-9', pid], check=True)
                    print(f"✓ Killed process {pid} on port {port}")
                except:
                    pass
    except:
        pass

def cleanup_ports():
    """Clean up ports 8000 and 3000"""
    print("🧹 Cleaning up existing processes...")
    
    # Kill by process name
    subprocess.run(['pkill', '-f', 'uvicorn'], stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-f', 'npm start'], stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-f', 'react-scripts'], stderr=subprocess.DEVNULL)
    
    # Kill by port
    kill_process_on_port(8000)
    kill_process_on_port(3000)
    
    time.sleep(2)
    print("✅ Cleanup complete")

def cleanup(backend_proc, frontend_proc):
    print("\n🚪 Stopping TRINETRA...")
    if backend_proc:
        backend_proc.terminate()
        try:
            backend_proc.wait(timeout=5)
        except:
            backend_proc.kill()
    if frontend_proc:
        frontend_proc.terminate()
        try:
            frontend_proc.wait(timeout=5)
        except:
            frontend_proc.kill()
    
    # Final cleanup
    kill_process_on_port(8000)
    kill_process_on_port(3000)
    print("✓ Shutdown complete")

def main():
    print("🕵️  TRINETRA - Dark Web Intelligence System")
    print("=" * 50)
    
    # Clean up any existing processes first
    cleanup_ports()
    
    backend_proc = None
    frontend_proc = None
    
    try:
        # Start backend
        print("🚀 Starting Backend...")
        os.chdir("/home/vector/darknet_crawler")
        backend_proc = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "api.main:app",
            "--host", "0.0.0.0", "--port", "8000"
        ])
        
        time.sleep(3)  # Wait for backend to start
        
        # Start frontend
        print("⚛️  Starting Frontend...")
        os.chdir("/home/vector/darknet_crawler/frontend")
        frontend_proc = subprocess.Popen(["npm", "start"])
        
        print("\n" + "=" * 50)
        print("🟢 TRINETRA is running!")
        print("🌐 Frontend: http://localhost:3000")
        print("🔌 Backend:  http://localhost:8000")
        print("=" * 50)
        print("Press Ctrl+C to stop\n")
        
        # Wait for processes
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        cleanup(backend_proc, frontend_proc)
    except Exception as e:
        print(f"Error: {e}")
        cleanup(backend_proc, frontend_proc)

if __name__ == "__main__":
    main()
