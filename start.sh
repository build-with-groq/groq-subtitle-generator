#!/bin/bash

# Video Subtitle Generator - Startup Script

echo "Starting Video Subtitle Generator..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "   FFmpeg is not installed. Please install FFmpeg first."
    echo "   macOS: brew install ffmpeg"
    echo "   Ubuntu/Debian: sudo apt install ffmpeg"
    echo "   Windows: Download from https://ffmpeg.org/download.html"
    exit 1
fi

# Check if backend environment exists
if [ ! -d "backend/venv" ]; then
    echo "Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# Check if backend dependencies are installed
if [ ! -f "backend/venv/lib/python*/site-packages/fastapi" ]; then
    echo "Installing Python dependencies..."
    cd backend
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Check if frontend dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo ".env file not found. Creating basic configuration..."
    cat > backend/.env << 'EOF'
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Model Configuration  
GROQ_MODEL=qwen/qwen3-32b
GROQ_WHISPER_MODEL=whisper-large-v3
EOF
    echo "Please edit backend/.env and add your Groq API key before continuing."
    echo "GROQ_API_KEY=your_groq_api_key_here"
    echo ""
    echo "You can get a free API key at: https://groq.com"
    echo ""
    read -p "Press Enter after setting up your API key..."
fi

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "🔧 Starting backend server..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 3

# Check if backend is running
if ! curl -s http://localhost:8000 > /dev/null; then
    echo "Backend failed to start. Check the logs above."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "Backend server started at http://localhost:8000"

echo "Starting frontend server..."
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
echo "Waiting for frontend to start..."
sleep 5

echo "Frontend server started at http://localhost:3000"
echo ""
echo "   Video Subtitle Generator is ready!"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 