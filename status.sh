#!/bin/bash

# Text-to-MongoDB Query Application - Status Script
# Check status of Server and UI

echo "=========================================="
echo "Application Status"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# PID files
SERVER_PID_FILE="$SCRIPT_DIR/.server.pid"
UI_PID_FILE="$SCRIPT_DIR/.ui.pid"

# Check MongoDB
echo "🗄️  MongoDB:"
if pgrep -x "mongod" > /dev/null; then
    echo -e "   ${GREEN}✓ Running${NC}"
else
    echo -e "   ${RED}✗ Not running${NC}"
fi

# Check Server
echo ""
echo "🖥️  Server (Port 5000):"
if [ -f "$SERVER_PID_FILE" ]; then
    SERVER_PID=$(cat "$SERVER_PID_FILE")
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo -e "   ${GREEN}✓ Running (PID: $SERVER_PID)${NC}"
        
        # Check if server is responding
        if curl -s http://localhost:5000/health > /dev/null 2>&1; then
            echo -e "   ${GREEN}✓ Responding to requests${NC}"
        else
            echo -e "   ${YELLOW}⚠️  Process running but not responding${NC}"
        fi
    else
        echo -e "   ${RED}✗ Not running (stale PID file)${NC}"
    fi
else
    # Check if something else is on port 5000
    if lsof -ti:5000 > /dev/null 2>&1; then
        PID=$(lsof -ti:5000)
        echo -e "   ${YELLOW}⚠️  Port in use by PID: $PID (not managed by start.sh)${NC}"
    else
        echo -e "   ${RED}✗ Not running${NC}"
    fi
fi

# Check UI
echo ""
echo "🎨 UI (Port 8000):"
if [ -f "$UI_PID_FILE" ]; then
    UI_PID=$(cat "$UI_PID_FILE")
    if ps -p $UI_PID > /dev/null 2>&1; then
        echo -e "   ${GREEN}✓ Running (PID: $UI_PID)${NC}"
        
        # Check if UI is responding
        if curl -s http://localhost:8000 > /dev/null 2>&1; then
            echo -e "   ${GREEN}✓ Responding to requests${NC}"
        else
            echo -e "   ${YELLOW}⚠️  Process running but not responding${NC}"
        fi
    else
        echo -e "   ${RED}✗ Not running (stale PID file)${NC}"
    fi
else
    # Check if something else is on port 8000
    if lsof -ti:8000 > /dev/null 2>&1; then
        PID=$(lsof -ti:8000)
        echo -e "   ${YELLOW}⚠️  Port in use by PID: $PID (not managed by start.sh)${NC}"
    else
        echo -e "   ${RED}✗ Not running${NC}"
    fi
fi

# Check configuration
echo ""
echo "⚙️  Configuration:"
if [ -f "$SCRIPT_DIR/server/.env" ]; then
    echo -e "   ${GREEN}✓ .env file exists${NC}"
    
    # Validate configuration
    cd "$SCRIPT_DIR/server"
    if [ -d "venv" ]; then
        source venv/bin/activate
        python3 -c "from config import Config; Config.validate()" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "   ${GREEN}✓ Configuration valid${NC}"
        else
            echo -e "   ${RED}✗ Configuration invalid${NC}"
        fi
    fi
else
    echo -e "   ${RED}✗ .env file not found${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo "📊 Quick Links:"
echo "   UI:     http://localhost:8000"
echo "   API:    http://localhost:5000"
echo "   Health: http://localhost:5000/health"
echo ""
echo "📝 Logs:"
echo "   Server: tail -f $SCRIPT_DIR/server.log"
echo "   UI:     tail -f $SCRIPT_DIR/ui.log"
echo ""
echo "🔧 Commands:"
echo "   Start:  ./start.sh"
echo "   Stop:   ./stop.sh"
echo "   Status: ./status.sh"
echo "=========================================="
echo ""
