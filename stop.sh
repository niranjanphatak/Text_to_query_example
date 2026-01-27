#!/bin/bash

# Text-to-MongoDB Query Application - Stop Script
# Stops both Server and UI

echo "=========================================="
echo "Stopping Application"
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

STOPPED_COUNT=0

# Stop server
if [ -f "$SERVER_PID_FILE" ]; then
    SERVER_PID=$(cat "$SERVER_PID_FILE")
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo "🛑 Stopping server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null
        sleep 1
        
        # Force kill if still running
        if ps -p $SERVER_PID > /dev/null 2>&1; then
            kill -9 $SERVER_PID 2>/dev/null
        fi
        
        echo -e "${GREEN}✓ Server stopped${NC}"
        STOPPED_COUNT=$((STOPPED_COUNT + 1))
    else
        echo -e "${YELLOW}⚠️  Server process not found${NC}"
    fi
    rm "$SERVER_PID_FILE"
else
    echo "ℹ️  No server PID file found"
fi

# Stop UI
if [ -f "$UI_PID_FILE" ]; then
    UI_PID=$(cat "$UI_PID_FILE")
    if ps -p $UI_PID > /dev/null 2>&1; then
        echo "🛑 Stopping UI (PID: $UI_PID)..."
        kill $UI_PID 2>/dev/null
        sleep 1
        
        # Force kill if still running
        if ps -p $UI_PID > /dev/null 2>&1; then
            kill -9 $UI_PID 2>/dev/null
        fi
        
        echo -e "${GREEN}✓ UI stopped${NC}"
        STOPPED_COUNT=$((STOPPED_COUNT + 1))
    else
        echo -e "${YELLOW}⚠️  UI process not found${NC}"
    fi
    rm "$UI_PID_FILE"
else
    echo "ℹ️  No UI PID file found"
fi

# Also kill any processes on ports 5000 and 8000 (cleanup)
echo ""
echo "🧹 Cleaning up ports..."
KILLED_5000=$(lsof -ti:5000 2>/dev/null)
if [ ! -z "$KILLED_5000" ]; then
    lsof -ti:5000 | xargs kill -9 2>/dev/null
    echo "  Killed process on port 5000"
    STOPPED_COUNT=$((STOPPED_COUNT + 1))
fi

KILLED_8000=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$KILLED_8000" ]; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    echo "  Killed process on port 8000"
    STOPPED_COUNT=$((STOPPED_COUNT + 1))
fi

echo ""
echo "=========================================="
if [ $STOPPED_COUNT -gt 0 ]; then
    echo -e "${GREEN}✅ Application stopped ($STOPPED_COUNT process(es))${NC}"
else
    echo -e "${YELLOW}ℹ️  No running processes found${NC}"
fi
echo "=========================================="
echo ""
