#!/usr/bin/env python3
"""
🌹 Legend Ultimate Bot - No Database Version
Simple, powerful group management bot
"""

import logging
import sys
import re
from datetime import datetime
from typing import Optional

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ApplicationBuilder
)

import config
from data_manager import data
from admin_commands import AdminCommands

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class LegendBot:
    def __init__(self):
        """Initialize the bot"""
        logger.info("Initializing Legend Ultimate Bot...")
        
        # Initialize handlers
        self.admin = AdminCommands()
        
        # Create application
        try:
            self.app = (
                ApplicationBuilder()
                .token(config.Config.BOT_TOKEN)
                .concurrent_updates(True)
                .build()
            )
        except Exception as e:
            logger.error(f"Failed to create application: {e}")
            sys.exit(1)
        
        # Register handlers
        self._register_handlers()
        
        # Set bot commands
        self.commands = self._get_bot_commands()
        
        # Error handler
        self.app.add_error_handler(self.error_handler)
        
        logger.info("Bot initialized successfully!")
    
    def _register_handlers(self):
        """Register all command handlers"""
        
        # ============ BASIC COMMANDS ============
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("id", self.id_command))
        
        # ============ ADMIN COMMANDS ============
        # Sudo management
        self.app.add_handler(CommandHandler("addsudo", self.admin.add_sudo))
        self.app.add_handler(CommandHandler("rmsudo", self.admin.remove_sudo))
        self.app.add_handler(CommandHandler("sudolist", self.admin.sudo_list))
        
        # Global bans
        self.app.add_handler(CommandHandler("gban", self.admin.global_ban))
        self.app.add_handler(CommandHandler("ungban", self.admin.global_unban))
        self.app.add_handler(CommandHandler("gbanlist", self.admin.gban_list))
        
        # Federation
        self.app.add_handler(CommandHandler("newfed", self.admin.new_federation))
        self.app.add_handler(CommandHandler("delfed", self.admin.delete_federation))
        self.app.add_handler(CommandHandler("fedinfo", self.admin.fed_info))
        self.app.add_handler(CommandHandler("fban", self.admin.fed_ban))
        self.app.add_handler(CommandHandler("unfban", self.admin.fed_unban))
        
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
        
        # Clean messages
        self.app.add_handler(CommandHandler("cleanmsg", self.admin.clean_messages))
        self.app.add_handler(CommandHandler("keepmsg", self.admin.keep_messages))
        self.app.add_handler(CommandHandler("nocleanmsg", self.admin.keep_messages))
        self.app.add_handler(CommandHandler("cleanmsgtypes", self.admin.clean_message_types))
        
        # Connections
        self.app.add_handler(CommandHandler("connect", self.admin.connect_chat))
        self.app.add_handler(CommandHandler("disconnect", self.admin.disconnect_chat))
        self.app.add_handler(CommandHandler("reconnect", self.admin.reconnect_chat))
        self.app.add_handler(CommandHandler("connection", self.admin.connection_info))
        
        # ============ MODERATION COMMANDS ============
        self.app.add_handler(CommandHandler("ban", self.admin.ban_user))
        self.app.add_handler(CommandHandler("unban", self.admin.unban_user))
        self.app.add_handler(CommandHandler("mute", self.admin.mute_user))
        self.app.add_handler(CommandHandler("unmute", self.admin.unmute_user))
        self.app.add_handler(CommandHandler("kick", self.admin.kick_user))
        self.app.add_handler(CommandHandler("warn", self.admin.warn_user))
        self.app.add_handler(CommandHandler("unwarn", self.admin.unwarn_user))
        self.app.add_handler(CommandHandler("warns", self.admin.show_warns))
        self.app.add_handler(CommandHandler("del", self.admin.delete_message))
        self.app.add_handler(CommandHandler("purge", self.admin.purge_messages))
        
        # ============ FILTERS & NOTES ============
        self.app.add_handler(CommandHandler("filter", self.admin.add_filter))
        self.app.add_handler(CommandHandler("stop", self.admin.remove_filter))
        self.app.add_handler(CommandHandler("filters", self.admin.list_filters))
        
        self.app.add_handler(CommandHandler("save", self.admin.save_note))
        self.app.add_handler(CommandHandler("get", self.admin.get_note))
        self.app.add_handler(CommandHandler("clear", self.admin.clear_note))
        self.app.add_handler(CommandHandler("notes", self.admin.list_notes))
        
        # ============ UTILITY COMMANDS ============
        self.app.add_handler(CommandHandler("rules", self.admin.show_rules))
        self.app.add_handler(CommandHandler("setrules", self.admin.set_rules))
        self.app.add_handler(CommandHandler("report", self.admin.report_user))
        self.app.add_handler(CommandHandler("settings", self.admin.chat_settings))
        
        # ============ MESSAGE HANDLERS ============
        # Handle filters in messages
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.admin.handle_filter_message
            )
        )
        
        # Handle new members for welcome
        self.app.add_handler(
            MessageHandler(
                filters.StatusUpdate.NEW_CHAT_MEMBERS,
                self.admin.handle_new_members
            )
        )
        
        # Handle left members for goodbye
        self.app.add_handler(
            MessageHandler(
                filters.StatusUpdate.LEFT_CHAT_MEMBERS,
                self.admin.handle_left_members
            )
        )
        
        # Alternative command prefix !
        self.app.add_handler(
            MessageHandler(
                filters.Regex(r'^!\w+'),
                self.handle_exclamation_command
            )
        )
    
    def _get_bot_commands(self):
        """Get bot commands for BotFather"""
        return [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Get help"),
            BotCommand("id", "Get ID"),
            BotCommand("ban", "Ban user"),
            BotCommand("unban", "Unban user"),
            BotCommand("mute", "Mute user"),
            BotCommand("unmute", "Unmute user"),
            BotCommand("warn", "Warn user"),
            BotCommand("kick", "Kick user"),
            BotCommand("setwelcome", "Set welcome"),
            BotCommand("setgoodbye", "Set goodbye"),
            BotCommand("rules", "Show rules"),
            BotCommand("report", "Report user"),
            BotCommand("filter", "Add filter"),
            BotCommand("save", "Save note"),
            BotCommand("cleanmsg", "Auto-delete messages"),
            BotCommand("connect", "Connect to chat"),
        ]
    
    # ============ BASIC COMMAND HANDLERS ============
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        chat = update.effective_chat
        
        # Save user data
        data.update_user(
            user.id,
            first_name=user.first_name,
            last_name=user.last_name or "",
            username=user.username or ""
        )
        
        welcome_msg = config.Messages.START_MSG.format(
            support_chat=config.Config.SUPPORT_CHAT
        )
        
        await update.message.reply_text(
            welcome_msg,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await update.message.reply_text(
            config.Messages.HELP_MSG,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    async def id_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /id command"""
        user = update.effective_user
        chat = update.effective_chat
        
        response = f"""
👤 *Your ID:* `{user.id}`
💬 *Chat ID:* `{chat.id}`

"""
        
        if user.username:
            response += f"📱 *Username:* @{user.username}\n"
        
        if chat.type != "private":
            response += f"📛 *Chat Title:* {chat.title}\n"
            response += f"👥 *Chat Type:* {chat.type}\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def handle_exclamation_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle commands with ! prefix"""
        message = update.message.text
        command = message.split()[0][1:]  # Remove "!"
        
        # Simulate command handling
        # In practice, you would route this to appropriate handlers
        await update.message.reply_text(
            f"Command `!{command}` received.\n"
            f"I also support `/` prefix for commands.",
            parse_mode='Markdown'
        )
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception: {context.error}", exc_info=context.error)
        
        # Try to send error to user
        try:
            if update and hasattr(update, 'message') and update.message:
                await update.message.reply_text(
                    f"❌ An error occurred:\n`{context.error}`",
                    parse_mode='Markdown'
                )
        except:
            pass
    
    async def post_init(self, application: Application):
        """Run after bot initialization"""
        try:
            # Set bot commands
            await application.bot.set_my_commands(self.commands)
            
            # Get bot info
            me = await application.bot.get_me()
            config.Config.BOT_USERNAME = me.username
            
            logger.info(f"Bot started as @{me.username}")
            logger.info(f"Owner: {config.Config.OWNER_ID}")
            logger.info(f"Sudo users: {len(config.Config.SUDO_USERS)}")
            
            # Load additional sudo users from data
            data_sudo_users = data.get_all_sudo_users()
            if data_sudo_users:
                logger.info(f"Data sudo users: {len(data_sudo_users)}")
            
            print("\n" + "="*50)
            print("🌹 LEGEND BOT STARTED SUCCESSFULLY!")
            print("="*50)
            print(f"Bot: @{me.username}")
            print(f"Owner: {config.Config.OWNER_ID}")
            print(f"Support: {config.Config.SUPPORT_CHAT}")
            print("="*50 + "\n")
            
        except Exception as e:
            logger.error(f"Post-init error: {e}")
    
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
            data.cleanup()  # Save all data
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            data.cleanup()  # Save all data before exit
            sys.exit(1)

def main():
    """Main entry point"""
    print("\n" + "="*50)
    print("🌹 LEGEND ULTIMATE BOT - No Database Version")
    print("="*50)
    print(f"Version: 2.0.0")
    print(f"Python: {sys.version}")
    print("="*50 + "\n")
    
    # Create and run bot
    bot = LegendBot()
    bot.run()

if __name__ == "__main__":
    main()
