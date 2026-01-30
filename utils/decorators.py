from functools import wraps
from typing import Callable
from telegram import Update
from telegram.ext import ContextTypes
import config
from utils.helpers import is_admin, is_owner, log_action

def admin_only(func: Callable):
    """Decorator to restrict command to admins only"""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_user:
            return
        
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Check if user is owner
        if is_owner(user_id):
            return await func(update, context, *args, **kwargs)
        
        # Check if user is admin in chat
        if is_admin(chat_id, user_id, context):
            return await func(update, context, *args, **kwargs)
        
        # Not admin
        if update.message:
            await update.message.reply_text("❌ You need to be an admin to use this command!")
        
        log_action("ADMIN_COMMAND_DENIED", user_id, chat_id, func.__name__)
        return
    
    return wrapped

def owner_only(func: Callable):
    """Decorator to restrict command to bot owner only"""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_user:
            return
        
        user_id = update.effective_user.id
        
        if is_owner(user_id):
            return await func(update, context, *args, **kwargs)
        
        # Not owner
        if update.message:
            await update.message.reply_text("❌ This command is only for the bot owner!")
        
        log_action("OWNER_COMMAND_DENIED", user_id, func.__name__)
        return
    
    return wrapped

def sudo_only(func: Callable):
    """Decorator to restrict command to sudo users"""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_user:
            return
        
        user_id = update.effective_user.id
        
        if user_id in config.Config.SUDO_USERS or is_owner(user_id):
            return await func(update, context, *args, **kwargs)
        
        # Not sudo
        if update.message:
            await update.message.reply_text("❌ This command is only for sudo users!")
        
        return
    
    return wrapped

def dev_only(func: Callable):
    """Decorator to restrict command to dev users"""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_user:
            return
        
        user_id = update.effective_user.id
        
        if user_id in config.Config.DEV_USERS or is_owner(user_id):
            return await func(update, context, *args, **kwargs)
        
        # Not dev
        if update.message:
            await update.message.reply_text("❌ This command is only for developers!")
        
        return
    
    return wrapped

def private_chat_only(func: Callable):
    """Decorator to restrict command to private chats only"""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_chat.type != "private":
            await update.message.reply_text("❌ This command can only be used in private chat!")
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapped

def group_chat_only(func: Callable):
    """Decorator to restrict command to groups only"""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_chat.type not in ["group", "supergroup"]:
            await update.message.reply_text("❌ This command can only be used in groups!")
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapped
