import os
import sys
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Config:
    # ===== BOT TOKEN (REQUIRED) =====
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN is required in .env file!")
        print("Get it from: https://t.me/BotFather")
        sys.exit(1)
    
    # ===== BOT INFO =====
    BOT_NAME = "Legend Ultimate Bot 🌹"
    BOT_USERNAME = None  # Will be set at runtime
    
    # ===== OWNER & ADMINS =====
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    SUDO_USERS = []
    if os.getenv("SUDO_USERS"):
        SUDO_USERS = [int(x.strip()) for x in os.getenv("SUDO_USERS").split(",") if x.strip().isdigit()]
    
    # ===== SUPPORT =====
    SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "@RoseSupportChat")
    UPDATE_CHANNEL = os.getenv("UPDATE_CHANNEL", "@RoseUpdateChannel")
    
    # ===== BOT SETTINGS =====
    DEL_CMDS = os.getenv("DEL_CMDS", "true").lower() == "true"
    WORKERS = int(os.getenv("WORKERS", "8"))
    
    # ===== PATHS =====
    DATA_DIR = "data"
    
    # ===== CLEAN MESSAGE TYPES =====
    CLEAN_TYPES = ["action", "note", "warn", "report", "filter"]
    
    # ===== LOCK TYPES =====
    LOCK_TYPES = [
        "text", "audio", "voice", "video", "photo", "document",
        "sticker", "gif", "game", "poll", "forward", "location",
        "contact", "url", "bot", "inline", "all"
    ]

class Messages:
    # Welcome message
    START_MSG = """
🌹 *Welcome to Legend Ultimate Bot!*

I'm an advanced group management bot with powerful features:
• Moderation tools (ban, mute, warn, kick)
• Welcome/Goodbye messages
• Filters and notes system
• Federation support
• Anti-spam protection
• And much more!

Use /help to see all commands.
Support: {support_chat}
"""
    
    HELP_MSG = """
🌹 *Legend Ultimate Bot - Help Menu*

*Admin Commands:*
• /ban [user] [reason] - Ban a user
• /unban [user] - Unban a user
• /mute [user] [time] - Mute a user
• /unmute [user] - Unmute a user
• /warn [user] [reason] - Warn a user
• /unwarn [user] - Remove warning
• /kick [user] - Kick a user
• /del - Delete command message

*Welcome/Goodbye:*
• /setwelcome [text] - Set welcome message
• /unsetwelcome - Remove welcome message
• /setgoodbye [text] - Set goodbye message
• /unsetgoodbye - Remove goodbye message

*Sudo Management (Owner Only):*
• /addsudo [user] - Add user to sudo
• /rmsudo [user] - Remove user from sudo
• /sudolist - List sudo users

*Global Bans:*
• /gban [user] [reason] - Global ban
• /ungban [user] - Remove global ban
• /gbanlist - List globally banned users

*Federation:*
• /newfed [name] - Create federation
• /delfed [fedid] - Delete federation
• /fedinfo [fedid] - Federation info
• /fban [user] [reason] - Ban in federation
• /unfban [user] - Unban in federation

*Locks:*
• /lock [type] - Lock media type
• /unlock [type] - Unlock media type
• /lockall - Lock all types
• /unlockall - Unlock all types
• /locktypes - Show lockable types

*Clean Messages:*
• /cleanmsg [type] - Auto-delete bot messages
• /keepmsg [type] - Stop auto-deleting
• /cleanmsgtypes - List deletable types

*Connections:*
• /connect [chat] - Connect to chat
• /disconnect - Disconnect from chat
• /reconnect - Reconnect
• /connection - Show connection info

*Filters & Notes:*
• /filter [word] [reply] - Add filter
• /stop [word] - Remove filter
• /filters - List filters
• /save [name] [content] - Save note
• /get [name] - Get note
• /clear [name] - Delete note
• /notes - List notes

*Other Commands:*
• /start - Start the bot
• /help - This message
• /id - Get user/chat ID
• /report [reason] - Report user
• /rules - Show chat rules
• /setrules [text] - Set rules
• /settings - Chat settings

*Note:* Commands also work with ! prefix
"""
    
    # Error messages
    NO_PERMISSION = "❌ You don't have permission to use this command!"
    USER_NOT_FOUND = "❌ User not found! Reply to a user or provide user ID/username."
    NOT_IN_GROUP = "❌ This command can only be used in groups!"
    NOT_IN_PRIVATE = "❌ This command can only be used in private chat!"
