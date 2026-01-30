#!/bin/bash

# Rose Ultimate Bot - Startup Script
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🌹 Legend Ultimate Bot Startup${NC}"
echo "================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found!${NC}"
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
    echo "Creating .env file..."
    cp .env.example .env
    echo -e "${RED}⚠️  Please edit .env file and add your BOT_TOKEN!${NC}"
    echo "Edit: nano .env"
    exit 1
fi

# Run bot
echo -e "${GREEN}Starting Legend Ultimate Bot...${NC}"
python3 bot.py
