import os
import sys
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

class Config:
    # ============ BOT CONFIG ============
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME: Optional[str] = None
    BOT_NAME: str = "Rose Ultimate Bot 🌹"
    
    # ============ API CONFIG ============
    API_ID: int = int(os.getenv("API_ID", 0))
    API_HASH: str = os.getenv("API_HASH", "")
    
    # ============ OWNER & ADMINS ============
    OWNER_ID: int = int(os.getenv("OWNER_ID", 0))
    SUDO_USERS: List[int] = [int(x) for x in os.getenv("SUDO_USERS", "").split(",") if x.isdigit()]
    DEV_USERS: List[int] = [int(x) for x in os.getenv("DEV_USERS", "").split(",") if x.isdigit()]
    
    # ============ DATABASE ============
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///rose_bot.db")
    MONGO_URI: str = os.getenv("MONGO_URI", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # ============ LOGGING ============
    LOG_CHANNEL: int = int(os.getenv("LOG_CHANNEL", 0))
    ERROR_LOG: int = int(os.getenv("ERROR_LOG", 0))
    
    # ============ SUPPORT ============
    SUPPORT_CHAT: str = os.getenv("SUPPORT_CHAT", "@RoseSupportChat")
    UPDATE_CHANNEL: str = os.getenv("UPDATE_CHANNEL", "@RoseUpdateChannel")
    SUPPORT_CHANNEL: str = os.getenv("SUPPORT_CHANNEL", "@RoseSupportChannel")
    
    # ============ BOT SETTINGS ============
    ALLOW_EXCL: bool = True  # Allow ! commands
    DEL_CMDS: bool = True    # Delete command messages
    WORKERS: int = int(os.getenv("WORKERS", 8))
    TIMEZONE: str = os.getenv("TIMEZONE", "UTC")
    
    # ============ FEDERATION ============
    FED_IDS: List[str] = [x for x in os.getenv("FED_IDS", "").split(",") if x]
    
    # ============ CACHE ============
    CACHE_TIME: int = int(os.getenv("CACHE_TIME", 300))
    
    # ============ ANTISPAM ============
    ANTISPAM_SERVICE: str = os.getenv("ANTISPAM_SERVICE", "cas").lower()
    
    @classmethod
    def validate(cls) -> bool:
        """Validate essential configuration"""
        if not cls.BOT_TOKEN:
            print("❌ ERROR: BOT_TOKEN is required in .env file!")
            print("Get it from: https://t.me/BotFather")
            return False
        
        if not cls.OWNER_ID:
            print("⚠️ WARNING: OWNER_ID not set. Some admin features may not work.")
        
        return True
    
    @classmethod
    def get_owner_ids(cls) -> List[int]:
        """Get all owner-level user IDs"""
        owners = [cls.OWNER_ID]
        owners.extend(cls.DEV_USERS)
        owners.extend(cls.SUDO_USERS)
        return list(set(filter(None, owners)))

# Validate config
if not Config.validate():
    sys.exit(1)
