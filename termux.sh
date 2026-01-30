#!/data/data/com.termux/files/usr/bin/bash

echo "🌹 Legend Bot Setup for Termux"
echo "=============================="

# Update packages
pkg update -y && pkg upgrade -y
pkg install python git -y

# Install Python packages
pip install --upgrade pip
pip install python-telegram-bot python-dotenv

# Clone or create project
if [ ! -d "rose-bot" ]; then
    git clone https://github.com/your-repo/rose-bot.git
    cd rose-bot
else
    cd rose-bot
fi

# Setup .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Please edit .env file: nano .env"
    echo "Add your BOT_TOKEN from @BotFather"
    read -p "Press Enter to continue..."
fi

# Run bot
echo "Starting Legend Bot..."
python bot.py
