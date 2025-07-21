#!/bin/bash

echo "🕵️  Starting TRINETRA..."
echo "🧹 Cleaning up any existing processes..."

# Kill any existing processes on these ports more aggressively
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true

# Kill processes using ports 8000 and 3000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Wait a moment for cleanup
sleep 2

echo "✅ Cleanup complete"

# Start backend in background
echo "🚀 Starting Backend on port 8000..."
cd /home/vector/darknet_crawler
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 3

# Start frontend in background  
echo "⚛️  Starting Frontend on port 3000..."
cd /home/vector/darknet_crawler/frontend
npm start &
FRONTEND_PID=$!

sleep 2

echo ""
echo "🟢 TRINETRA is running!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔌 Backend:  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping TRINETRA..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    pkill -f "uvicorn.*8000" 2>/dev/null
    pkill -f "npm.*start" 2>/dev/null
    echo "✓ Shutdown complete"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Wait for user to press Ctrl+C
while true; do
    sleep 1
done
