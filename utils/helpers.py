import re
import html
from typing import Optional, Union, List, Dict, Any
from datetime import datetime, timedelta
from telegram import User, Chat
from telegram.constants import ChatType
import config
from database import Session, Users, Chats

def get_user_info(user: User) -> Dict[str, Any]:
    """Get formatted user information"""
    return {
        'id': user.id,
        'name': user.full_name,
        'username': f"@{user.username}" if user.username else "No username",
        'mention': user.mention_html(user.full_name)
    }

def extract_user_id(text: str) -> Optional[int]:
    """Extract user ID from text (reply, mention, or ID)"""
    if not text:
        return None
    
    # Check if it's a reply
    match = re.match(r'^(\d+)$', text)
    if match:
        return int(match.group(1))
    
    # Check if it's a mention
    match = re.match(r'^@(\w+)$', text)
    if match:
        # Would need to resolve username to ID
        return None
    
    return None

def is_admin(chat_id: int, user_id: int, context) -> bool:
    """Check if user is admin in chat"""
    try:
        member = context.bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except:
        return False

def is_owner(user_id: int) -> bool:
    """Check if user is bot owner"""
    return user_id in config.Config.get_owner_ids()

def format_time(seconds: int) -> str:
    """Format seconds to human readable time"""
    periods = [
        ('year', 31536000),
        ('month', 2592000),
        ('day', 86400),
        ('hour', 3600),
        ('minute', 60),
        ('second', 1)
    ]
    
    result = []
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result.append(f"{period_value} {period_name}{'s' if period_value > 1 else ''}")
    
    return ', '.join(result[:2])

def parse_time(time_str: str) -> Optional[int]:
    """Parse time string like '5m', '2h', '1d' to seconds"""
    if not time_str:
        return None
    
    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800
    }
    
    match = re.match(r'^(\d+)([smhdw])$', time_str.lower())
    if match:
        value, unit = match.groups()
        return int(value) * multipliers.get(unit, 1)
    
    return None

def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])

def get_or_create_user(user_id: int, session=None) -> Users:
    """Get user from DB or create if not exists"""
    if session is None:
        session = Session()
    
    user = session.query(Users).filter_by(user_id=user_id).first()
    if not user:
        user = Users(user_id=user_id)
        session.add(user)
        session.commit()
    
    return user

def get_chat_info(chat_id: int, session=None) -> Optional[Chats]:
    """Get chat info from DB"""
    if session is None:
        session = Session()
    
    return session.query(Chats).filter_by(chat_id=chat_id).first()

def log_action(action: str, user_id: int, chat_id: int = 0, details: str = ""):
    """Log bot actions"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {action} | User: {user_id} | Chat: {chat_id}"
    if details:
        log_msg += f" | Details: {details}"
    print(log_msg)
