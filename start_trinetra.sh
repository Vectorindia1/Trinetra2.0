#!/bin/bash

# TRINETRA - Dark Web Intelligence System Startup Script
echo "🕵️  Starting TRINETRA - Dark Web Intelligence System..."
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to cleanup processes on exit
cleanup() {
    echo -e "\n${RED}🛑 Shutting down TRINETRA...${NC}"
    echo "Stopping all processes..."
    
    # Kill background processes
    if [[ ! -z "$BACKEND_PID" ]]; then
        kill $BACKEND_PID 2>/dev/null
        echo "✓ Backend API stopped"
    fi
    
    if [[ ! -z "$FRONTEND_PID" ]]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "✓ Frontend React server stopped"
    fi
    
    # Kill any remaining processes on ports 8000 and 3000
    pkill -f "uvicorn.*8000" 2>/dev/null
    pkill -f "react-scripts.*3000" 2>/dev/null
    
    echo "🕵️  TRINETRA shutdown complete."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if we're in the right directory
if [[ ! -f "api/main.py" ]] || [[ ! -d "frontend" ]]; then
    echo -e "${RED}❌ Error: Please run this script from the darknet_crawler directory${NC}"
    echo "Expected files: api/main.py and frontend/ directory"
    exit 1
fi

echo -e "${BLUE}🚀 Starting FastAPI Backend Server...${NC}"
cd /home/vector/darknet_crawler
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

echo -e "${BLUE}⚛️  Starting React Frontend Server...${NC}"
cd /home/vector/darknet_crawler/frontend
npm start &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 5

echo -e "${GREEN}=================================================="
echo -e "🕵️  TRINETRA is now running!"
echo -e "=================================================="
echo -e "🌐 Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "🔌 Backend:  ${GREEN}http://localhost:8000${NC}"
echo -e "📊 API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "=================================================="
echo -e "${BLUE}Press Ctrl+C to stop both servers${NC}"

# Keep script running and wait for processes
wait $BACKEND_PID $FRONTEND_PID
