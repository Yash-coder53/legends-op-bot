#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}"
echo "=================================="
echo "🌹 Legend Ultimate Bot - Starter"
echo "=================================="
echo -e "${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found! Install Python 3.8+${NC}"
    exit 1
fi

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Check .env
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env file and add your BOT_TOKEN!${NC}"
    echo "Get token from @BotFather on Telegram"
    echo "Run: nano .env"
    exit 1
fi

# Create data directory
mkdir -p data

# Run bot
echo -e "${GREEN}"
echo "=================================="
echo "Starting Legend Ultimate Bot..."
echo "=================================="
echo -e "${NC}"
python3 bot.py
