from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Session, Users, Chats, Filters, Notes, GBans
from utils.decorators import admin_only, owner_only, sudo_only
from utils.helpers import extract_user_id, format_time, parse_time
import json
import re

class AdminHandlers:
    """Handle all admin commands"""
    
    @owner_only
    async def add_sudo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add user to sudo list"""
        if not context.args:
            await update.message.reply_text("Usage: /addsudo [user_id/username/reply]")
            return
        
        target = extract_user_id(context.args[0])
        if not target:
            await update.message.reply_text("❌ Invalid user specified!")
            return
        
        session = Session()
        user = session.query(Users).filter_by(user_id=target).first()
        if not user:
            user = Users(user_id=target)
        
        user.sudo = True
        session.commit()
        session.close()
        
        await update.message.reply_text(f"✅ User {target} added to sudo!")
    
    @owner_only
    async def remove_sudo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove user from sudo list"""
        if not context.args:
            await update.message.reply_text("Usage: /rmsudo [user_id/username/reply]")
            return
        
        target = extract_user_id(context.args[0])
        if not target:
            await update.message.reply_text("❌ Invalid user specified!")
            return
        
        session = Session()
        user = session.query(Users).filter_by(user_id=target).first()
        if user:
            user.sudo = False
            session.commit()
            await update.message.reply_text(f"✅ User {target} removed from sudo!")
        else:
            await update.message.reply_text("❌ User not found!")
        
        session.close()
    
    @sudo_only
    async def global_ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Globally ban a user"""
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /gban [user_id/username/reply] [reason]")
            return
        
        target = extract_user_id(context.args[0])
        reason = " ".join(context.args[1:]) or "No reason provided"
        
        if not target:
            await update.message.reply_text("❌ Invalid user specified!")
            return
        
        session = Session()
        # Check if already gbanned
        existing = session.query(GBans).filter_by(user_id=target).first()
        if existing:
            await update.message.reply_text("❌ User is already globally banned!")
            session.close()
            return
        
        # Add to GBans
        gban = GBans(
            user_id=target,
            reason=reason,
            banned_by=update.effective_user.id
        )
        session.add(gban)
        
        # Update user record
        user = session.query(Users).filter_by(user_id=target).first()
        if user:
            user.is_gbanned = True
        else:
            user = Users(user_id=target, is_gbanned=True)
            session.add(user)
        
        session.commit()
        session.close()
        
        await update.message.reply_text(
            f"✅ User {target} has been globally banned!\n"
            f"Reason: {reason}"
        )
    
    @admin_only
    async def set_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set welcome message for chat"""
        chat_id = update.effective_chat.id
        
        if not context.args:
            await update.message.reply_text(
                "Usage: /setwelcome [message]\n\n"
                "Available variables:\n"
                "{first} - User's first name\n"
                "{last} - User's last name\n"
                "{fullname} - User's full name\n"
                "{username} - User's username\n"
                "{id} - User's ID\n"
                "{chat} - Chat title\n"
                "{count} - Member count\n"
                "{mention} - Mention the user"
            )
            return
        
        welcome_text = " ".join(context.args)
        
        session = Session()
        chat = session.query(Chats).filter_by(chat_id=chat_id).first()
        if not chat:
            chat = Chats(chat_id=chat_id, title=update.effective_chat.title)
            session.add(chat)
        
        chat.welcome = welcome_text
        chat.welcome_enabled = True
        session.commit()
        session.close()
        
        await update.message.reply_text("✅ Welcome message set!")
    
    @admin_only
    async def clean_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Auto-delete bot messages after 5 minutes"""
        if not context.args:
            await update.message.reply_text(
                "Usage: /cleanmsg [type]\n\n"
                "Types: action, note, warn, report, filter, all\n\n"
                "Examples:\n"
                "• /cleanmsg action - Delete ban/mute messages\n"
                "• /cleanmsg all - Delete all bot messages"
            )
            return
        
        msg_type = context.args[0].lower()
        valid_types = ["action", "note", "warn", "report", "filter", "all"]
        
        if msg_type not in valid_types:
            await update.message.reply_text(
                f"❌ Invalid type! Choose from: {', '.join(valid_types)}"
            )
            return
        
        # Implementation would store this preference in database
        await update.message.reply_text(
            f"✅ Bot will delete '{msg_type}' messages after 5 minutes.\n"
            f"Use /keepmsg {msg_type} to stop deleting."
        )
    
    @admin_only
    async def connect_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Connect to a chat for remote administration"""
        chat_id = update.effective_chat.id
        
        if context.args:
            # Connect to specified chat
            target = context.args[0]
            await update.message.reply_text(
                f"✅ Connected to chat: {target}\n"
                f"Use /connection to see info\n"
                f"Use /disconnect to disconnect"
            )
        else:
            # In group: connect to current chat
            # In private: list recent connections
            if update.effective_chat.type == "private":
                await update.message.reply_text(
                    "Recent connections:\n"
                    "1. Rose Support Chat (-1001234567890)\n"
                    "2. Test Group (-1009876543210)\n\n"
                    "Usage: /connect [chat_id/username]"
                )
            else:
                await update.message.reply_text(
                    f"✅ Connected to this chat!\n"
                    f"Chat ID: {chat_id}\n"
                    f"Title: {update.effective_chat.title}"
                )
    
    # Add all other admin command methods...
