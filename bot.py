#!/usr/bin/env python3
"""
🌹 Legends Ultimate Bot - Advanced Group Management Bot
Combines all features from images and requested commands
"""

import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ApplicationBuilder
)

import config
from database import Session, Users, Chats, init_db
from utils.helpers import get_user_info, log_action
from utils.decorators import admin_only, owner_only, sudo_only
from handlers.admin_handlers import AdminHandlers
from handlers.user_handlers import UserHandlers
from handlers.mod_handlers import ModHandlers
from handlers.fed_handlers import FedHandlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('rose_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class LegendUltimateBot:
    def __init__(self):
        """Initialize the bot with all handlers"""
        logger.info("Initializing Legends Ultimate Bot...")
        
        # Initialize database
        init_db()
        
        # Initialize handlers
        self.admin = AdminHandlers()
        self.user = UserHandlers()
        self.mod = ModHandlers()
        self.fed = FedHandlers()
        
        # Create application with error handling
        try:
            self.app = (
                ApplicationBuilder()
                .token(config.Config.BOT_TOKEN)
                .pool_timeout(30)
                .connect_timeout(30)
                .read_timeout(30)
                .write_timeout(30)
                .build()
            )
        except Exception as e:
            logger.error(f"Failed to create application: {e}")
            sys.exit(1)
        
        # Register all handlers
        self._register_handlers()
        
        # Set bot commands for BotFather
        self._setup_bot_commands()
        
        # Error handler
        self.app.add_error_handler(self.error_handler)
        
        logger.info("Bot initialized successfully!")
    
    def _register_handlers(self):
        """Register all command handlers"""
        
        # ============ BASIC COMMANDS ============
        self.app.add_handler(CommandHandler("start", self.user.start))
        self.app.add_handler(CommandHandler("help", self.user.help))
        self.app.add_handler(CommandHandler("id", self.user.get_id))
        
        # ============ ADMIN COMMANDS ============
        # Sudo management
        self.app.add_handler(CommandHandler("addsudo", self.admin.add_sudo))
        self.app.add_handler(CommandHandler("rmsudo", self.admin.remove_sudo))
        self.app.add_handler(CommandHandler("sudolist", self.admin.sudo_list))
        
        # Global bans
        self.app.add_handler(CommandHandler("gban", self.admin.global_ban))
        self.app.add_handler(CommandHandler("ungban", self.admin.global_unban))
        self.app.add_handler(CommandHandler("fban", self.fed.fed_ban))
        self.app.add_handler(CommandHandler("unfban", self.fed.fed_unban))
        self.app.add_handler(CommandHandler("gbanlist", self.admin.gban_list))
        
        # Welcome/Goodbye
        self.app.add_handler(CommandHandler("setwelcome", self.admin.set_welcome))
        self.app.add_handler(CommandHandler("unsetwelcome", self.admin.unset_welcome))
        self.app.add_handler(CommandHandler("setgoodbye", self.admin.set_goodbye))
        self.app.add_handler(CommandHandler("unsetgoodbye", self.admin.unset_goodbye))
        self.app.add_handler(CommandHandler("welcome", self.admin.show_welcome))
        self.app.add_handler(CommandHandler("goodbye", self.admin.show_goodbye))
        
        # Locks
        self.app.add_handler(CommandHandler("lock", self.admin.lock_chat))
        self.app.add_handler(CommandHandler("unlock", self.admin.unlock_chat))
        self.app.add_handler(CommandHandler("lockall", self.admin.lock_all))
        self.app.add_handler(CommandHandler("unlockall", self.admin.unlock_all))
        self.app.add_handler(CommandHandler("locks", self.admin.show_locks))
        self.app.add_handler(CommandHandler("locktypes", self.admin.lock_types))
        
        # Clean messages (from images)
        self.app.add_handler(CommandHandler("cleanmsg", self.admin.clean_messages))
        self.app.add_handler(CommandHandler("keepmsg", self.admin.keep_messages))
        self.app.add_handler(CommandHandler("nocleanmsg", self.admin.keep_messages))
        self.app.add_handler(CommandHandler("cleanmsgtypes", self.admin.clean_message_types))
        
        # Connections (from images)
        self.app.add_handler(CommandHandler("connect", self.admin.connect_chat))
        self.app.add_handler(CommandHandler("disconnect", self.admin.disconnect_chat))
        self.app.add_handler(CommandHandler("reconnect", self.admin.reconnect_chat))
        self.app.add_handler(CommandHandler("connection", self.admin.connection_info))
        self.app.add_handler(CommandHandler("connections", self.admin.connections_list))
        
        # ============ MODERATION COMMANDS ============
        self.app.add_handler(CommandHandler("ban", self.mod.ban_user))
        self.app.add_handler(CommandHandler("unban", self.mod.unban_user))
        self.app.add_handler(CommandHandler("mute", self.mod.mute_user))
        self.app.add_handler(CommandHandler("unmute", self.mod.unmute_user))
        self.app.add_handler(CommandHandler("kick", self.mod.kick_user))
        self.app.add_handler(CommandHandler("warn", self.mod.warn_user))
        self.app.add_handler(CommandHandler("unwarn", self.mod.unwarn_user))
        self.app.add_handler(CommandHandler("warns", self.mod.show_warns))
        self.app.add_handler(CommandHandler("del", self.mod.delete_message))
        self.app.add_handler(CommandHandler("purge", self.mod.purge_messages))
        
        # ============ FEDERATION COMMANDS ============
        self.app.add_handler(CommandHandler("newfed", self.fed.new_federation))
        self.app.add_handler(CommandHandler("delfed", self.fed.delete_federation))
        self.app.add_handler(CommandHandler("fedinfo", self.fed.fed_info))
        self.app.add_handler(CommandHandler("fedadmins", self.fed.fed_admins))
        self.app.add_handler(CommandHandler("fpromote", self.fed.fed_promote))
        self.app.add_handler(CommandHandler("fdemote", self.fed.fed_demote))
        self.app.add_handler(CommandHandler("fedchats", self.fed.fed_chats))
        
        # ============ UTILITY COMMANDS ============
        self.app.add_handler(CommandHandler("rules", self.user.show_rules))
        self.app.add_handler(CommandHandler("setrules", self.admin.set_rules))
        self.app.add_handler(CommandHandler("report", self.user.report_user))
        self.app.add_handler(CommandHandler("settings", self.admin.chat_settings))
        
        # ============ FILTERS & NOTES ============
        self.app.add_handler(CommandHandler("filter", self.admin.add_filter))
        self.app.add_handler(CommandHandler("stop", self.admin.remove_filter))
        self.app.add_handler(CommandHandler("filters", self.admin.list_filters))
        
        self.app.add_handler(CommandHandler("save", self.admin.save_note))
        self.app.add_handler(CommandHandler("get", self.user.get_note))
        self.app.add_handler(CommandHandler("clear", self.admin.clear_note))
        self.app.add_handler(CommandHandler("notes", self.user.list_notes))
        
        # ============ MESSAGE HANDLERS ============
        # Handle all non-command text messages for filters
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.admin.handle_filter
            )
        )
        
        # Handle new chat members for welcome
        self.app.add_handler(
            MessageHandler(
                filters.StatusUpdate.NEW_CHAT_MEMBERS,
                self.admin.handle_new_members
            )
        )
        
        # Handle left chat members for goodbye
        self.app.add_handler(
            MessageHandler(
                filters.StatusUpdate.LEFT_CHAT_MEMBERS,
                self.admin.handle_left_members
            )
        )
        
        logger.info(f"Registered {len(self.app.handlers)} handlers")
    
    def _setup_bot_commands(self):
        """Setup bot commands for BotFather menu"""
        self.commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Get help with commands"),
            BotCommand("id", "Get user/chat ID"),
            
            # Admin commands
            BotCommand("ban", "Ban a user"),
            BotCommand("unban", "Unban a user"),
            BotCommand("mute", "Mute a user"),
            BotCommand("unmute", "Unmute a user"),
            BotCommand("warn", "Warn a user"),
            BotCommand("kick", "Kick a user"),
            BotCommand("del", "Delete a message"),
            
            # Settings
            BotCommand("setwelcome", "Set welcome message"),
            BotCommand("setgoodbye", "Set goodbye message"),
            BotCommand("rules", "Show chat rules"),
            BotCommand("settings", "Chat settings"),
            
            # Filters & Notes
            BotCommand("filter", "Add a filter"),
            BotCommand("filters", "List filters"),
            BotCommand("save", "Save a note"),
            BotCommand("notes", "List notes"),
            
            # Clean messages
            BotCommand("cleanmsg", "Auto-delete bot messages"),
            BotCommand("cleanmsgtypes", "List deletable types"),
            
            # Connections
            BotCommand("connect", "Connect to a chat"),
            BotCommand("connection", "Show connection info"),
            
            # Federation
            BotCommand("newfed", "Create new federation"),
            BotCommand("fedinfo", "Federation info"),
            
            # Report
            BotCommand("report", "Report a user"),
        ]
    
    async def set_bot_commands(self):
        """Set bot commands in BotFather"""
        try:
            await self.app.bot.set_my_commands(self.commands)
            logger.info("Bot commands set successfully!")
        except Exception as e:
            logger.error(f"Failed to set bot commands: {e}")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the bot"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Log error details
        if update and hasattr(update, 'effective_user'):
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id if update.effective_chat else 0
            logger.error(f"User: {user_id}, Chat: {chat_id}")
        
        # Send error to log channel if configured
        if config.Config.LOG_CHANNEL:
            try:
                error_msg = (
                    f"❌ *Bot Error*\n\n"
                    f"• Error: `{context.error}`\n"
                    f"• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                
                if update and hasattr(update, 'effective_user'):
                    error_msg += f"• User: {update.effective_user.id}\n"
                
                await context.bot.send_message(
                    config.Config.LOG_CHANNEL,
                    error_msg,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to send error to log channel: {e}")
    
    async def post_init(self, application: Application):
        """Run after bot is initialized"""
        await self.set_bot_commands()
        
        # Set bot username in config
        me = await application.bot.get_me()
        config.Config.BOT_USERNAME = me.username
        
        logger.info(f"Bot started as @{me.username}")
        logger.info(f"Owner ID: {config.Config.OWNER_ID}")
        logger.info(f"Sudo users: {len(config.Config.SUDO_USERS)}")
        logger.info("🌹 Legend Ultimate Bot is ready!")
    
    def run(self):
        """Start the bot"""
        try:
            logger.info("Starting bot polling...")
            
            # Add post-init callback
            self.app.post_init = self.post_init
            
            # Start polling
            self.app.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                close_loop=False
            )
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            sys.exit(1)

def main():
    """Main entry point"""
    print("\n" + "="*50)
    print("🌹 LEGEND ULTIMATE BOT - Advanced Group Management")
    print("="*50)
    print(f"Version: 3.0.0")
    print(f"Python: {sys.version}")
    print(f"Owner ID: {config.Config.OWNER_ID}")
    print("="*50 + "\n")
    
    # Create and run bot
    bot = LegendUltimateBot()
    bot.run()

if __name__ == "__main__":
    main()
