import re
from telegram.ext import ContextTypes
import config

def extract_user_id(text: str):
    """Extract user ID from text"""
    if not text:
        return None
    
    # Numeric ID
    if text.isdigit():
        return int(text)
    
    # Username (simplified)
    if text.startswith('@'):
        return None  # Would need to resolve
    
    return None

def is_owner(user_id: int) -> bool:
    """Check if user is owner"""
    return user_id == config.Config.OWNER_ID

def is_sudo(user_id: int) -> bool:
    """Check if user is sudo"""
    return user_id in config.Config.SUDO_USERS or is_owner(user_id)

async def is_admin(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is admin in chat"""
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except:
        return False

def format_time(seconds: int) -> str:
    """Format seconds to human readable"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds//60}m"
    elif seconds < 86400:
        return f"{seconds//3600}h"
    else:
        return f"{seconds//86400}d"

def parse_time(time_str: str):
    """Parse time string to seconds"""
    if not time_str:
        return None
    
    multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    match = re.match(r'^(\d+)([smhd])$', time_str.lower())
    
    if match:
        value, unit = match.groups()
        return int(value) * multipliers.get(unit, 1)
    
    return None
