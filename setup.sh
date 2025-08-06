#!/bin/bash

# Video Subtitle Generator - Setup Script

echo "🛠️  Setting up Video Subtitle Generator..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "   Python 3 is not installed. Please install Python 3.8+"
    echo "   macOS: brew install python"
    echo "   Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "   Windows: Download from https://python.org"
    exit 1
fi

# Check if uv is installed, install if not
if ! command -v uv &> /dev/null; then
    echo "📦 uv package manager not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Source the environment to make uv available
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # Check if uv is now available
    if ! command -v uv &> /dev/null; then
        echo "❌ Failed to install uv. Please install manually:"
        echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "   Then restart your terminal and run this script again."
        exit 1
    fi
    echo "✅ uv installed successfully"
else
    echo "✅ uv package manager found"
fi


# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "   Node.js is not installed. Please install Node.js 18+"
    echo "   macOS: brew install node"
    echo "   Ubuntu/Debian: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs"
    echo "   Windows: Download from https://nodejs.org"
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

echo "All system dependencies are installed!"
echo ""

# Create backend virtual environment
echo "Setting up Python virtual environment..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
uv pip install -r requirements.txt
echo "Python dependencies installed"

cd ..

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install
echo "Node.js dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f "backend/.env" ]; then
    echo "Creating environment configuration..."
    cat > backend/.env << 'EOF'
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Model Configuration  
GROQ_MODEL=qwen/qwen3-32b
GROQ_WHISPER_MODEL=whisper-large-v3
EOF
    echo "Environment file created"
else
    echo "Environment file already exists"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env and add your Groq API key:"
echo "   GROQ_API_KEY=your_groq_api_key_here"
echo ""
echo "2. Get a free API key at: https://groq.com"
echo ""
echo "3. Run the application:"
echo "   ./start.sh"
echo ""
echo "For more information, see README.md" 