#!/bin/bash

# Text-to-MongoDB Query Application - Complete Startup Script
# Starts both Server and UI

echo "=========================================="
echo "Text-to-MongoDB Query Application"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVER_DIR="$SCRIPT_DIR/server"
UI_DIR="$SCRIPT_DIR/ui"

# PID files
SERVER_PID_FILE="$SCRIPT_DIR/.server.pid"
UI_PID_FILE="$SCRIPT_DIR/.ui.pid"

# Check if MongoDB is running
echo "🔍 Checking MongoDB..."
if ! pgrep -x "mongod" > /dev/null; then
    echo -e "${YELLOW}⚠️  MongoDB is not running${NC}"
    echo "Starting MongoDB..."
    brew services start mongodb-community 2>/dev/null || {
        echo -e "${RED}❌ Could not start MongoDB automatically${NC}"
        echo -e "${YELLOW}Please start MongoDB manually:${NC}"
        echo "  brew services start mongodb-community"
        echo "  OR"
        echo "  docker run -d -p 27017:27017 --name mongodb mongo:latest"
        exit 1
    }
    sleep 2
fi
echo -e "${GREEN}✓ MongoDB is running${NC}"

# Check if virtual environment exists
if [ ! -d "$SERVER_DIR/venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    cd "$SERVER_DIR"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment and install dependencies
echo ""
echo "📥 Installing/updating dependencies..."
cd "$SERVER_DIR"
source venv/bin/activate
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Check if .env exists
if [ ! -f "$SERVER_DIR/.env" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    cp "$SERVER_DIR/.env.example" "$SERVER_DIR/.env"
    echo -e "${YELLOW}Created .env file from template${NC}"
    echo ""
    echo -e "${RED}IMPORTANT: Please edit server/.env and set ALL required values:${NC}"
    echo "  - OPENAI_API_KEY"
    echo "  - OPENAI_BASE_URL"
    echo "  - OPENAI_MODEL"
    echo "  - MONGO_URI"
    echo "  - DB_NAME"
    echo ""
    echo "Get your OpenAI API key from: https://platform.openai.com/api-keys"
    echo ""
    read -p "Press Enter after you've configured server/.env..."
fi

# Validate configuration
echo ""
echo "🔍 Validating configuration..."
cd "$SERVER_DIR"
python3 -c "from config import Config; Config.validate()" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Configuration validation failed${NC}"
    echo ""
    echo "Please ensure ALL required values are set in server/.env:"
    echo "  - MONGO_URI"
    echo "  - DB_NAME"
    echo "  - OPENAI_API_KEY"
    echo "  - OPENAI_BASE_URL"
    echo "  - OPENAI_MODEL"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ Configuration validated${NC}"

# Stop any existing instances
echo ""
echo "🛑 Stopping any existing instances..."
if [ -f "$SERVER_PID_FILE" ]; then
    OLD_PID=$(cat "$SERVER_PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        kill $OLD_PID 2>/dev/null
        echo "  Stopped old server (PID: $OLD_PID)"
    fi
    rm "$SERVER_PID_FILE"
fi

if [ -f "$UI_PID_FILE" ]; then
    OLD_PID=$(cat "$UI_PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        kill $OLD_PID 2>/dev/null
        echo "  Stopped old UI (PID: $OLD_PID)"
    fi
    rm "$UI_PID_FILE"
fi

# Also kill any processes on ports 5000 and 8000
lsof -ti:5000 | xargs kill -9 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 1

# Start the server in background
echo ""
echo "🚀 Starting server..."
cd "$SERVER_DIR"
source venv/bin/activate
nohup python app.py > "$SCRIPT_DIR/server.log" 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > "$SERVER_PID_FILE"
echo -e "${GREEN}✓ Server started (PID: $SERVER_PID)${NC}"
echo "  Logs: $SCRIPT_DIR/server.log"

# Wait for server to start
echo "  Waiting for server to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ Server is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}  ✗ Server failed to start${NC}"
        echo "  Check logs: tail -f $SCRIPT_DIR/server.log"
        exit 1
    fi
    sleep 1
done

# Start the UI in background
echo ""
echo "🎨 Starting UI..."
cd "$UI_DIR"
nohup python3 -m http.server 8000 > "$SCRIPT_DIR/ui.log" 2>&1 &
UI_PID=$!
echo $UI_PID > "$UI_PID_FILE"
echo -e "${GREEN}✓ UI started (PID: $UI_PID)${NC}"
echo "  Logs: $SCRIPT_DIR/ui.log"

# Wait for UI to start
echo "  Waiting for UI to be ready..."
for i in {1..10}; do
    if curl -s http://localhost:8000 > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ UI is ready${NC}"
        break
    fi
    sleep 1
done

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Application started successfully!${NC}"
echo "=========================================="
echo ""
echo "📊 Access the application:"
echo "  🌐 UI:     http://localhost:8000"
echo "  🔌 API:    http://localhost:5000"
echo "  ❤️  Health: http://localhost:5000/health"
echo ""
echo "📝 Logs:"
echo "  Server: tail -f $SCRIPT_DIR/server.log"
echo "  UI:     tail -f $SCRIPT_DIR/ui.log"
echo ""
echo "🛑 To stop the application:"
echo "  ./stop.sh"
echo ""
echo "=========================================="
echo ""

# Open browser automatically (optional)
read -p "Open browser automatically? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sleep 2
    open http://localhost:8000 2>/dev/null || xdg-open http://localhost:8000 2>/dev/null || echo "Please open http://localhost:8000 in your browser"
fi
