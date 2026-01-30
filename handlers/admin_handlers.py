import re
import html
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import config
from data_manager import data
from utils.helpers import (
    extract_user_id, 
    is_admin, 
    is_owner, 
    is_sudo, 
    format_time, 
    parse_time
)

class AdminCommands:
    """All admin command handlers"""
    
    # ===== HELPER METHODS =====
    def _check_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if user is admin"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Owner and sudo can do anything
        if is_owner(user_id) or is_sudo(user_id):
            return True
        
        # Check if admin in chat
        if chat_id and update.effective_chat.type != "private":
            return is_admin(chat_id, user_id, context)
        
        return False
    
    def _check_owner(self, update: Update) -> bool:
        """Check if user is owner"""
        return is_owner(update.effective_user.id)
    
    def _check_sudo(self, update: Update) -> bool:
        """Check if user is sudo"""
        return is_sudo(update.effective_user.id)
    
    def _get_target_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
        """Extract target user from command"""
        if update.message.reply_to_message:
            return update.message.reply_to_message.from_user.id
        
        if context.args:
            # Try to extract user ID
            target = extract_user_id(context.args[0])
            if target:
                return target
            
            # Check for username
            match = re.match(r'^@(\w+)$', context.args[0])
            if match:
                # In real implementation, you'd resolve username to ID
                # For now, return None
                return None
        
        return None
    
    # ===== OWNER COMMANDS =====
    async def add_sudo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add user to sudo: /addsudo [user]"""
        if not self._check_owner(update):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /addsudo [user_id/username/reply]")
            return
        
        target = self._get_target_user(update, context)
        if not target:
            await update.message.reply_text("❌ Invalid user specified!")
            return
        
        # Add to sudo
        data.update_user(target, sudo=True)
        
        # Add to config SUDO_USERS if not already
        if target not in config.Config.SUDO_USERS:
            config.Config.SUDO_USERS.append(target)
        
        await update.message.reply_text(f"✅ User {target} added to sudo!")
    
    async def remove_sudo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove user from sudo: /rmsudo [user]"""
        if not self._check_owner(update):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /rmsudo [user_id/username/reply]")
            return
        
        target = self._get_target_user(update, context)
        if not target:
            await update.message.reply_text("❌ Invalid user specified!")
            return
        
        # Remove from sudo
        data.update_user(target, sudo=False)
        
        # Remove from config SUDO_USERS
        if target in config.Config.SUDO_USERS:
            config.Config.SUDO_USERS.remove(target)
        
        await update.message.reply_text(f"✅ User {target} removed from sudo!")
    
    async def sudo_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all sudo users: /sudolist"""
        if not self._check_owner(update):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        sudo_users = data.get_all_sudo_users()
        
        if not sudo_users:
            await update.message.reply_text("📝 No sudo users.")
            return
        
        response = "👑 *Sudo Users:*\n\n"
        for user_id in sudo_users[:50]:  # Show first 50
            user_data = data.get_user(user_id)
            name = user_data.get('first_name', 'Unknown')
            username = user_data.get('username', '')
            
            if username:
                response += f"• {name} (@{username}) - `{user_id}`\n"
            else:
                response += f"• {name} - `{user_id}`\n"
        
        if len(sudo_users) > 50:
            response += f"\n... and {len(sudo_users) - 50} more."
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    # ===== GLOBAL BAN COMMANDS =====
    async def global_ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Globally ban user: /gban [user] [reason]"""
        if not self._check_sudo(update):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /gban [user] [reason]")
            return
        
        target = self._get_target_user(update, context)
        if not target:
            await update.message.reply_text("❌ Invalid user specified!")
            return
        
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
        
        # Check if already gbanned
        if data.is_gbanned(target):
            await update.message.reply_text("❌ User is already globally banned!")
            return
        
        # Add global ban
        data.add_gban(target, reason, update.effective_user.id)
        
        await update.message.reply_text(
            f"✅ User {target} globally banned!\n"
            f"Reason: {reason}"
        )
    
    async def global_unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove global ban: /ungban [user]"""
        if not self._check_sudo(update):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /ungban [user]")
            return
        
        target = self._get_target_user(update, context)
        if not target:
            await update.message.reply_text("❌ Invalid user specified!")
            return
        
        # Remove global ban
        if data.remove_gban(target):
            await update.message.reply_text(f"✅ User {target} removed from global ban!")
        else:
            await update.message.reply_text("❌ User is not globally banned!")
    
    async def gban_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List globally banned users: /gbanlist"""
        if not self._check_sudo(update):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        gbans = data.gbans
        
        if not gbans:
            await update.message.reply_text("📝 No globally banned users.")
            return
        
        response = "🔨 *Globally Banned Users:*\n\n"
        for user_id, ban_data in list(gbans.items())[:30]:  # Show first 30
            user_data = data.get_user(int(user_id))
            name = user_data.get('first_name', 'Unknown')
            reason = ban_data.get('reason', 'No reason')
            
            response += f"• {name} (`{user_id}`)\n"
            response += f"  Reason: {reason}\n\n"
        
        if len(gbans) > 30:
            response += f"... and {len(gbans) - 30} more."
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    # ===== FEDERATION COMMANDS =====
    async def new_federation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create new federation: /newfed [name]"""
        if not self._check_sudo(update):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /newfed [name]")
            return
        
        fed_name = " ".join(context.args)
        fed_id = data.create_fed(fed_name, update.effective_user.id)
        
        await update.message.reply_text(
            f"✅ Federation created!\n"
            f"Name: {fed_name}\n"
            f"ID: `{fed_id}`",
            parse_mode='Markdown'
        )
    
    async def delete_federation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete federation: /delfed [fedid]"""
        if not self._check_sudo(update):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /delfed [fed_id]")
            return
        
        fed_id = context.args[0]
        
        if data.delete_fed(fed_id, update.effective_user.id):
            await update.message.reply_text(f"✅ Federation `{fed_id}` deleted!")
        else:
            await update.message.reply_text(
                "❌ Federation not found or you're not the owner!"
            )
    
    async def fed_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get federation info: /fedinfo [fedid]"""
        if not context.args:
            await update.message.reply_text("Usage: /fedinfo [fed_id]")
            return
        
        fed_id = context.args[0]
        
        if fed_id not in data.feds:
            await update.message.reply_text("❌ Federation not found!")
            return
        
        fed = data.feds[fed_id]
        
        response = (
            f"🏛️ *Federation Info*\n\n"
            f"• Name: {fed['name']}\n"
            f"• ID: `{fed_id}`\n"
            f"• Owner: `{fed['owner_id']}`\n"
            f"• Admins: {len(fed['admins'])}\n"
            f"• Chats: {len(fed['chats'])}\n"
            f"• FBans: {len(fed['fbans'])}\n"
            f"• Created: {fed['created_at'][:10]}"
        )
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def fed_ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ban in federation: /fban [user] [reason]"""
        if not self._check_sudo(update):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /fban [fed_id] [user] [reason]")
            return
        
        fed_id = context.args[0]
        target = extract_user_id(context.args[1])
        reason = " ".join(context.args[2:]) if len(context.args) > 2 else "No reason"
        
        if not target:
            await update.message.reply_text("❌ Invalid user specified!")
            return
        
        if fed_id not in data.feds:
            await update.message.reply_text("❌ Federation not found!")
            return
        
        # Check if user is fed admin or owner
        fed = data.feds[fed_id]
        user_id = update.effective_user.id
        
        if user_id != fed['owner_id'] and user_id not in fed['admins']:
            await update.message.reply_text("❌ You're not admin in this federation!")
            return
        
        data.add_fban(fed_id, target, reason, user_id)
        
        await update.message.reply_text(
            f"✅ User {target} banned in federation {fed['name']}!\n"
            f"Reason: {reason}"
        )
    
    async def fed_unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unban in federation: /unfban [user]"""
        if not self._check_sudo(update):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /unfban [fed_id] [user]")
            return
        
        fed_id = context.args[0]
        target = extract_user_id(context.args[1])
        
        if not target:
            await update.message.reply_text("❌ Invalid user specified!")
            return
        
        if fed_id not in data.feds:
            await update.message.reply_text("❌ Federation not found!")
            return
        
        # Remove fban if exists
        target_str = str(target)
        if target_str in data.feds[fed_id]['fbans']:
            del data.feds[fed_id]['fbans'][target_str]
            data.save_feds()
            await update.message.reply_text(f"✅ User {target} unbanned from federation!")
        else:
            await update.message.reply_text("❌ User is not banned in this federation!")
    
    # ===== WELCOME/GOODBYE COMMANDS =====
    async def set_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set welcome message: /setwelcome [text]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        if not context.args:
            help_text = (
                "Usage: /setwelcome [message]\n\n"
                "Available variables:\n"
                "{first} - User's first name\n"
                "{last} - User's last name\n"
                "{fullname} - User's full name\n"
                "{username} - User's username\n"
                "{id} - User's ID\n"
                "{chat} - Chat title\n"
                "{count} - Member count\n"
                "{mention} - Mention the user\n\n"
                "Example:\n"
                "/setwelcome Welcome {first} to {chat}!"
            )
            await update.message.reply_text(help_text)
            return
        
        welcome_text = " ".join(context.args)
        chat_id = update.effective_chat.id
        
        data.update_chat(chat_id, welcome=welcome_text, welcome_enabled=True)
        
        await update.message.reply_text("✅ Welcome message set!")
    
    async def unset_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove welcome message: /unsetwelcome"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        chat_id = update.effective_chat.id
        data.update_chat(chat_id, welcome="", welcome_enabled=False)
        
        await update.message.reply_text("✅ Welcome message removed!")
    
    async def show_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current welcome: /welcome"""
        chat_id = update.effective_chat.id
        chat = data.get_chat(chat_id)
        
        if chat.get('welcome') and chat.get('welcome_enabled'):
            welcome = chat['welcome']
            response = f"📝 *Current Welcome Message:*\n\n{welcome}"
        else:
            response = "❌ No welcome message set for this chat."
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def set_goodbye(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set goodbye message: /setgoodbye [text]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        if not context.args:
            help_text = (
                "Usage: /setgoodbye [message]\n\n"
                "Available variables:\n"
                "{first} - User's first name\n"
                "{last} - User's last name\n"
                "{fullname} - User's full name\n"
                "{username} - User's username\n"
                "{id} - User's ID\n"
                "{chat} - Chat title\n"
                "{count} - Member count\n"
                "{mention} - Mention the user\n\n"
                "Example:\n"
                "/setgoodbye Goodbye {first}!"
            )
            await update.message.reply_text(help_text)
            return
        
        goodbye_text = " ".join(context.args)
        chat_id = update.effective_chat.id
        
        data.update_chat(chat_id, goodbye=goodbye_text, goodbye_enabled=True)
        
        await update.message.reply_text("✅ Goodbye message set!")
    
    async def unset_goodbye(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove goodbye message: /unsetgoodbye"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        chat_id = update.effective_chat.id
        data.update_chat(chat_id, goodbye="", goodbye_enabled=False)
        
        await update.message.reply_text("✅ Goodbye message removed!")
    
    async def show_goodbye(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current goodbye: /goodbye"""
        chat_id = update.effective_chat.id
        chat = data.get_chat(chat_id)
        
        if chat.get('goodbye') and chat.get('goodbye_enabled'):
            goodbye = chat['goodbye']
            response = f"📝 *Current Goodbye Message:*\n\n{goodbye}"
        else:
            response = "❌ No goodbye message set for this chat."
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def handle_new_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle new chat members (welcome)"""
        chat_id = update.effective_chat.id
        chat = data.get_chat(chat_id)
        
        if not chat.get('welcome_enabled') or not chat.get('welcome'):
            return
        
        for member in update.message.new_chat_members:
            # Don't welcome bots
            if member.is_bot:
                continue
            
            welcome_text = chat['welcome']
            
            # Replace variables
            replacements = {
                '{first}': member.first_name,
                '{last}': member.last_name or '',
                '{fullname}': member.full_name,
                '{username}': f"@{member.username}" if member.username else member.first_name,
                '{id}': str(member.id),
                '{chat}': update.effective_chat.title,
                '{count}': str(update.effective_chat.get_member_count()),
                '{mention}': member.mention_html(member.first_name)
            }
            
            for key, value in replacements.items():
                welcome_text = welcome_text.replace(key, value)
            
            try:
                await update.message.reply_text(
                    welcome_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
            except Exception as e:
                print(f"Error sending welcome: {e}")
    
    async def handle_left_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle left chat members (goodbye)"""
        chat_id = update.effective_chat.id
        chat = data.get_chat(chat_id)
        
        if not chat.get('goodbye_enabled') or not chat.get('goodbye'):
            return
        
        for member in update.message.left_chat_members:
            # Don't say goodbye to bots
            if member.is_bot:
                continue
            
            goodbye_text = chat['goodbye']
            
            # Replace variables
            replacements = {
                '{first}': member.first_name,
                '{last}': member.last_name or '',
                '{fullname}': member.full_name,
                '{username}': f"@{member.username}" if member.username else member.first_name,
                '{id}': str(member.id),
                '{chat}': update.effective_chat.title,
                '{count}': str(update.effective_chat.get_member_count()),
                '{mention}': member.mention_html(member.first_name)
            }
            
            for key, value in replacements.items():
                goodbye_text = goodbye_text.replace(key, value)
            
            try:
                await update.message.reply_text(
                    goodbye_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
            except Exception as e:
                print(f"Error sending goodbye: {e}")
    
    # ===== LOCK COMMANDS =====
    async def lock_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lock media type: /lock [type]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: /lock [type]\n"
                "Use /locktypes to see available types"
            )
            return
        
        lock_type = context.args[0].lower()
        
        if lock_type not in config.Config.LOCK_TYPES:
            await update.message.reply_text(
                f"❌ Invalid lock type!\n"
                f"Use /locktypes to see available types"
            )
            return
        
        chat_id = update.effective_chat.id
        chat = data.get_chat(chat_id)
        
        lock_types = chat.get('lock_types', [])
        if lock_type not in lock_types:
            lock_types.append(lock_type)
            data.update_chat(chat_id, lock_types=lock_types)
        
        await update.message.reply_text(f"✅ Locked `{lock_type}`!")
    
    async def unlock_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unlock media type: /unlock [type]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        if not context.args:
            await update.message.reply_text(
                "Usage: /unlock [type]\n"
                "Use /locktypes to see available types"
            )
            return
        
        lock_type = context.args[0].lower()
        
        chat_id = update.effective_chat.id
        chat = data.get_chat(chat_id)
        
        lock_types = chat.get('lock_types', [])
        if lock_type in lock_types:
            lock_types.remove(lock_type)
            data.update_chat(chat_id, lock_types=lock_types)
        
        await update.message.reply_text(f"✅ Unlocked `{lock_type}`!")
    
    async def lock_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lock all media types: /lockall"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        chat_id = update.effective_chat.id
        data.update_chat(chat_id, is_locked=True)
        
        await update.message.reply_text("✅ All media types locked!")
    
    async def unlock_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unlock all media types: /unlockall"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        chat_id = update.effective_chat.id
        data.update_chat(chat_id, is_locked=False, lock_types=[])
        
        await update.message.reply_text("✅ All media types unlocked!")
    
    async def show_locks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current locks: /locks"""
        chat_id = update.effective_chat.id
        chat = data.get_chat(chat_id)
        
        if chat.get('is_locked'):
            response = "🔒 *Chat is fully locked!*\n"
            response += "Use /unlockall to unlock everything."
        else:
            lock_types = chat.get('lock_types', [])
            if lock_types:
                response = "🔒 *Current Locks:*\n"
                for lock_type in lock_types:
                    response += f"• `{lock_type}`\n"
                response += "\nUse /unlock [type] to unlock."
            else:
                response = "🔓 *No active locks.*\n"
                response += "Use /lock [type] to lock something."
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def lock_types(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show lockable types: /locktypes"""
        types_text = "🔒 *Lockable Types:*\n\n"
        
        types = config.Config.LOCK_TYPES
        for i in range(0, len(types), 3):
            line_types = types[i:i+3]
            types_text += " • " + " • ".join([f"`{t}`" for t in line_types]) + "\n"
        
        types_text += "\n*Usage:* `/lock [type]` or `/unlock [type]`"
        
        await update.message.reply_text(types_text, parse_mode='Markdown')
    
    # ===== CLEAN MESSAGE COMMANDS (FROM IMAGES) =====
    async def clean_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Auto-delete bot messages: /cleanmsg [type]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if not context.args:
            response = (
                "🗑️ *Clean Bot Messages*\n\n"
                "Usage: `/cleanmsg [type]`\n\n"
                "*Types:*\n"
                "• `action` - Ban/mute/kick messages\n"
                "• `note` - Note replies\n"
                "• `warn` - Warning messages\n"
                "• `report` - Report messages\n"
                "• `filter` - Filter triggers\n"
                "• `all` - All of the above\n\n"
                "*Examples:*\n"
                "• `/cleanmsg action` - Delete ban messages after 5 min\n"
                "• `/cleanmsg all` - Delete all bot messages"
            )
            await update.message.reply_text(response, parse_mode='Markdown')
            return
        
        msg_type = context.args[0].lower()
        valid_types = config.Config.CLEAN_TYPES + ["all"]
        
        if msg_type not in valid_types:
            await update.message.reply_text(
                f"❌ Invalid type! Use one of: {', '.join(valid_types)}"
            )
            return
        
        await update.message.reply_text(
            f"✅ Bot will delete `{msg_type}` messages after 5 minutes.\n"
            f"Use `/keepmsg {msg_type}` to stop deleting.",
            parse_mode='Markdown'
        )
    
    async def keep_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stop auto-deleting: /keepmsg [type]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /keepmsg [type]\nUse /cleanmsgtypes to see types")
            return
        
        msg_type = context.args[0].lower()
        
        await update.message.reply_text(
            f"✅ Bot will stop deleting `{msg_type}` messages.",
            parse_mode='Markdown'
        )
    
    async def clean_message_types(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List cleanable types: /cleanmsgtypes"""
        response = (
            "🗑️ *Cleanable Message Types:*\n\n"
            "• `action` - Ban/mute/kick/unban/unmute messages\n"
            "• `note` - Note reply messages\n"
            "• `warn` - Warning messages\n"
            "• `report` - Report messages\n"
            "• `filter` - Filter trigger messages\n"
            "• `all` - All of the above\n\n"
            "*Example:* `/cleanmsg action`\n"
            "Delete all ban/mute messages after 5 minutes"
        )
        await update.message.reply_text(response, parse_mode='Markdown')
    
    # ===== CONNECTION COMMANDS (FROM IMAGES) =====
    async def connect_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Connect to chat: /connect [chat]"""
        user_id = update.effective_user.id
        
        if context.args:
            # Connect to specified chat
            target = context.args[0]
            
            # Store connection
            data.add_connection(user_id, 0, target)  # 0 for unknown chat_id
            
            await update.message.reply_text(
                f"✅ Connected to chat: `{target}`\n"
                f"Use /connection to see info\n"
                f"Use /disconnect to disconnect",
                parse_mode='Markdown'
            )
        
        else:
            # In group: connect to current chat
            # In private: list recent connections
            if update.effective_chat.type == "private":
                connections = data.get_connections(user_id)
                
                if not connections:
                    response = (
                        "📡 *No recent connections.*\n\n"
                        "Usage: `/connect [chat_id/username]`\n\n"
                        "*Examples:*\n"
                        "• `/connect -1001234567890`\n"
                        "• `/connect @RoseSupportChat`"
                    )
                else:
                    response = "📡 *Recent Connections:*\n\n"
                    for i, conn in enumerate(connections[-5:], 1):
                        response += f"{i}. {conn.get('chat_title', 'Unknown')}\n"
                    
                    response += "\nUse `/connect [chat]` to connect to a new chat."
                
                await update.message.reply_text(response, parse_mode='Markdown')
            
            else:
                # In a group, connect to this chat
                chat_id = update.effective_chat.id
                chat_title = update.effective_chat.title
                
                data.add_connection(user_id, chat_id, chat_title)
                
                await update.message.reply_text(
                    f"✅ Connected to this chat!\n"
                    f"Chat: {chat_title}\n"
                    f"ID: `{chat_id}`",
                    parse_mode='Markdown'
                )
    
    async def disconnect_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Disconnect from chat: /disconnect"""
        user_id = update.effective_user.id
        
        if context.args and context.args[0].isdigit():
            chat_id = int(context.args[0])
            data.remove_connection(user_id, chat_id)
            await update.message.reply_text(f"✅ Disconnected from chat `{chat_id}`!")
        else:
            data.remove_connection(user_id)
            await update.message.reply_text("✅ Disconnected from all chats!")
    
    async def reconnect_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reconnect to previous chat: /reconnect"""
        user_id = update.effective_user.id
        connections = data.get_connections(user_id)
        
        if not connections:
            await update.message.reply_text("❌ No previous connections found!")
            return
        
        # Get the last connection
        last_conn = connections[-1]
        
        await update.message.reply_text(
            f"✅ Reconnected to:\n"
            f"Chat: {last_conn.get('chat_title', 'Unknown')}\n"
            f"ID: `{last_conn.get('chat_id', 'Unknown')}`",
            parse_mode='Markdown'
        )
    
    async def connection_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show connection info: /connection"""
        user_id = update.effective_user.id
        connections = data.get_connections(user_id)
        
        if not connections:
            await update.message.reply_text(
                "📡 *No active connection.*\n"
                "Use `/connect` to connect to a chat.",
                parse_mode='Markdown'
            )
            return
        
        # Show the most recent connection
        conn = connections[-1]
        
        response = (
            "📡 *Connection Information:*\n\n"
            f"• **Chat:** {conn.get('chat_title', 'Unknown')}\n"
            f"• **ID:** `{conn.get('chat_id', 'Unknown')}`\n"
            f"• **Type:** Remote Admin\n"
            f"• **Connected:** {conn.get('connected_at', 'Unknown')[:10]}\n\n"
            "Use `/connect` to change connection\n"
            "Use `/disconnect` to disconnect"
        )
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    # ===== MODERATION COMMANDS =====
    async def ban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ban user: /ban [user] [reason]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        target = self._get_target_user(update, context)
        if not target:
            await update.message.reply_text("❌ Please reply to a user or provide user ID!")
            return
        
        reason = " ".join(context.args[1:]) if context.args and len(context.args) > 1 else "No reason"
        
        try:
            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=target,
                revoke_messages=True
            )
            
            # Log the ban
            data.update_user(target, is_banned=True)
            
            response = f"✅ User banned!\n"
            if reason != "No reason":
                response += f"Reason: {reason}"
            
            await update.message.reply_text(response)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to ban user: {e}")
    
    async def unban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unban user: /unban [user]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        target = self._get_target_user(update, context)
        if not target:
            await update.message.reply_text("❌ Please reply to a user or provide user ID!")
            return
        
        try:
            await context.bot.unban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=target,
                only_if_banned=True
            )
            
            # Update user data
            data.update_user(target, is_banned=False)
            
            await update.message.reply_text("✅ User unbanned!")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to unban user: {e}")
    
    async def mute_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mute user: /mute [user] [time]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        target = self._get_target_user(update, context)
        if not target:
            await update.message.reply_text("❌ Please reply to a user or provide user ID!")
            return
        
        # Parse mute time
        mute_time = None
        if context.args and len(context.args) > 1:
            mute_time = parse_time(context.args[1])
        
        # Default: 24 hours
        until_date = datetime.now() + timedelta(hours=24)
        if mute_time:
            until_date = datetime.now() + timedelta(seconds=mute_time)
        
        reason = " ".join(context.args[2:]) if context.args and len(context.args) > 2 else "No reason"
        
        try:
            await context.bot.restrict_chat_member(
                chat_id=update.effective_chat.id,
                user_id=target,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False
                ),
                until_date=until_date
            )
            
            time_text = "permanently" if not mute_time else f"for {format_time(mute_time)}"
            response = f"✅ User muted {time_text}!\n"
            if reason != "No reason":
                response += f"Reason: {reason}"
            
            await update.message.reply_text(response)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to mute user: {e}")
    
    async def unmute_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unmute user: /unmute [user]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        target = self._get_target_user(update, context)
        if not target:
            await update.message.reply_text("❌ Please reply to a user or provide user ID!")
            return
        
        try:
            await context.bot.restrict_chat_member(
                chat_id=update.effective_chat.id,
                user_id=target,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
            )
            
            await update.message.reply_text("✅ User unmuted!")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to unmute user: {e}")
    
    async def kick_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Kick user: /kick [user] [reason]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        target = self._get_target_user(update, context)
        if not target:
            await update.message.reply_text("❌ Please reply to a user or provide user ID!")
            return
        
        reason = " ".join(context.args[1:]) if context.args and len(context.args) > 1 else "No reason"
        
        try:
            await context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=target,
                until_date=datetime.now() + timedelta(seconds=30)  # 30 second ban = kick
            )
            
            await context.bot.unban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=target
            )
            
            response = f"✅ User kicked!\n"
            if reason != "No reason":
                response += f"Reason: {reason}"
            
            await update.message.reply_text(response)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to kick user: {e}")
    
    async def warn_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Warn user: /warn [user] [reason]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        target = self._get_target_user(update, context)
        if not target:
            await update.message.reply_text("❌ Please reply to a user or provide user ID!")
            return
        
        reason = " ".join(context.args[1:]) if context.args and len(context.args) > 1 else "No reason"
        
        # Add warn
        warn_id = data.add_warn(
            target,
            update.effective_chat.id,
            reason,
            update.effective_user.id
        )
        
        user_warns = data.get_user_warns(target, update.effective_chat.id)
        warn_count = len(user_warns)
        
        response = f"⚠️ User warned! ({warn_count}/3)\n"
        if reason:
            response += f"Reason: {reason}\n"
        
        # Check if should ban (3 warns)
        if warn_count >= 3:
            try:
                await context.bot.ban_chat_member(
                    chat_id=update.effective_chat.id,
                    user_id=target,
                    revoke_messages=True
                )
                response += "\n🚫 User banned (3 warnings reached)!"
            except Exception as e:
                response += f"\n❌ Failed to auto-ban: {e}"
        
        await update.message.reply_text(response)
    
    async def unwarn_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove warning: /unwarn [user] [warn_id]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        target = self._get_target_user(update, context)
        if not target:
            await update.message.reply_text("❌ Please reply to a user or provide user ID!")
            return
        
        # Get all warns for this user
        user_warns = data.get_user_warns(target, update.effective_chat.id)
        
        if not user_warns:
            await update.message.reply_text("❌ User has no warnings!")
            return
        
        # If warn_id provided, remove specific warn
        if context.args and len(context.args) > 1:
            warn_id = context.args[1]
            if data.remove_warn(warn_id, update.effective_chat.id):
                await update.message.reply_text(f"✅ Warning removed!")
            else:
                await update.message.reply_text("❌ Warning not found!")
        else:
            # Remove the last warn
            last_warn = user_warns[-1]
            if data.remove_warn(last_warn['id'], update.effective_chat.id):
                await update.message.reply_text(f"✅ Last warning removed!")
            else:
                await update.message.reply_text("❌ Failed to remove warning!")
    
    async def show_warns(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user warnings: /warns [user]"""
        target = self._get_target_user(update, context)
        if not target:
            await update.message.reply_text("❌ Please reply to a user or provide user ID!")
            return
        
        user_warns = data.get_user_warns(target, update.effective_chat.id)
        
        if not user_warns:
            await update.message.reply_text("✅ User has no warnings!")
            return
        
        user_data = data.get_user(target)
        user_name = user_data.get('first_name', 'Unknown')
        
        response = f"⚠️ *Warnings for {user_name}:* ({len(user_warns)}/3)\n\n"
        
        for i, warn in enumerate(user_warns, 1):
            response += f"{i}. {warn.get('reason', 'No reason')}\n"
            response += f"   By: `{warn.get('warned_by', 'Unknown')}`\n"
            response += f"   At: {warn.get('warned_at', '')[:16]}\n"
            response += f"   ID: `{warn.get('id', '')}`\n\n"
        
        response += "Use `/unwarn [user] [warn_id]` to remove a warning."
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def delete_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete message: /del"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Reply to a message to delete it!")
            return
        
        try:
            await update.message.reply_to_message.delete()
            await update.message.delete()
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to delete message: {e}")
    
    async def purge_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Purge messages: /purge [count]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ Reply to a message to start purge from!")
            return
        
        try:
            count = 50  # Default
            if context.args and context.args[0].isdigit():
                count = min(int(context.args[0]), 100)  # Max 100 messages
            
            # Get message IDs to delete
            start_id = update.message.reply_to_message.message_id
            end_id = update.message.message_id
            
            # Delete messages in reverse order
            deleted = 0
            for msg_id in range(end_id, start_id - 1, -1):
                try:
                    await context.bot.delete_message(
                        chat_id=update.effective_chat.id,
                        message_id=msg_id
                    )
                    deleted += 1
                    
                    # Limit to count
                    if deleted >= count:
                        break
                        
                except:
                    continue
            
            # Send confirmation (will be deleted after 5 seconds)
            msg = await update.effective_chat.send_message(f"✅ Purged {deleted} messages!")
            
            # Delete confirmation after 5 seconds
            await asyncio.sleep(5)
            await msg.delete()
            
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to purge messages: {e}")
    
    # ===== FILTER COMMANDS =====
    async def add_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add filter: /filter [word] [reply]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /filter [keyword] [reply text]\n"
                "Or reply to a message with: /filter [keyword]"
            )
            return
        
        keyword = context.args[0].lower()
        
        if update.message.reply_to_message:
            # Use replied message content
            if update.message.reply_to_message.text:
                content = update.message.reply_to_message.text
            else:
                content = "[Media message]"
        else:
            # Use text after keyword
            content = " ".join(context.args[1:])
        
        chat_id = update.effective_chat.id
        
        # Check if filter already exists
        existing = data.get_filter(chat_id, keyword)
        if existing:
            await update.message.reply_text(f"❌ Filter `{keyword}` already exists!")
            return
        
        # Add filter
        data.add_filter(
            chat_id,
            keyword,
            content,
            user_id=update.effective_user.id
        )
        
        await update.message.reply_text(f"✅ Filter `{keyword}` added!")
    
    async def remove_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove filter: /stop [word]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /stop [keyword]")
            return
        
        keyword = context.args[0].lower()
        chat_id = update.effective_chat.id
        
        if data.remove_filter(chat_id, keyword):
            await update.message.reply_text(f"✅ Filter `{keyword}` removed!")
        else:
            await update.message.reply_text(f"❌ Filter `{keyword}` not found!")
    
    async def list_filters(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List filters: /filters"""
        chat_id = update.effective_chat.id
        filters = data.get_chat_filters(chat_id)
        
        if not filters:
            await update.message.reply_text("📝 No filters in this chat.")
            return
        
        response = "📝 *Filters in this chat:*\n\n"
        for keyword in sorted(filters.keys()):
            response += f"• `{keyword}`\n"
        
        response += "\nUse `/filter [word] [reply]` to add more."
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def handle_filter_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle filter triggers in messages"""
        chat_id = update.effective_chat.id
        message_text = update.message.text.lower()
        
        filters = data.get_chat_filters(chat_id)
        
        for keyword, filter_data in filters.items():
            if keyword in message_text:
                content = filter_data.get('content', '')
                if content:
                    await update.message.reply_text(content)
                break
    
    # ===== NOTE COMMANDS =====
    async def save_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save note: /save [name] [content]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /save [name] [content]\n"
                "Or reply to a message with: /save [name]"
            )
            return
        
        name = context.args[0].lower()
        
        if update.message.reply_to_message:
            # Use replied message content
            if update.message.reply_to_message.text:
                content = update.message.reply_to_message.text
            else:
                content = "[Media message]"
        else:
            # Use text after name
            content = " ".join(context.args[1:])
        
        chat_id = update.effective_chat.id
        
        # Check if note already exists
        existing = data.get_note(chat_id, name)
        if existing:
            await update.message.reply_text(f"❌ Note `{name}` already exists!")
            return
        
        # Add note
        data.add_note(
            chat_id,
            name,
            content,
            user_id=update.effective_user.id
        )
        
        await update.message.reply_text(f"✅ Note `{name}` saved!")
    
    async def get_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get note: /get [name]"""
        if not context.args:
            await update.message.reply_text("Usage: /get [note_name]")
            return
        
        name = context.args[0].lower()
        chat_id = update.effective_chat.id
        
        note = data.get_note(chat_id, name)
        if not note:
            await update.message.reply_text(f"❌ Note `{name}` not found!")
            return
        
        content = note.get('content', '')
        await update.message.reply_text(content)
    
    async def clear_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete note: /clear [name]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /clear [note_name]")
            return
        
        name = context.args[0].lower()
        chat_id = update.effective_chat.id
        
        if data.remove_note(chat_id, name):
            await update.message.reply_text(f"✅ Note `{name}` deleted!")
        else:
            await update.message.reply_text(f"❌ Note `{name}` not found!")
    
    async def list_notes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List notes: /notes"""
        chat_id = update.effective_chat.id
        notes = data.get_chat_notes(chat_id)
        
        if not notes:
            await update.message.reply_text("📝 No notes in this chat.")
            return
        
        response = "📝 *Notes in this chat:*\n\n"
        for name in sorted(notes.keys()):
            response += f"• `{name}`\n"
        
        response += "\nUse `/get [name]` to get a note."
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    # ===== OTHER COMMANDS =====
    async def show_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show rules: /rules"""
        chat_id = update.effective_chat.id
        chat = data.get_chat(chat_id)
        
        rules = chat.get('rules', '')
        
        if rules:
            response = f"📜 *Chat Rules:*\n\n{rules}"
        else:
            response = "📜 No rules set for this chat.\nAdmins can set rules with /setrules"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def set_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set rules: /setrules [text]"""
        if not self._check_admin(update, context):
            await update.message.reply_text(config.Messages.NO_PERMISSION)
            return
        
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /setrules [rules text]")
            return
        
        rules_text = " ".join(context.args)
        chat_id = update.effective_chat.id
        
        data.update_chat(chat_id, rules=rules_text)
        
        await update.message.reply_text("✅ Rules set!")
    
    async def report_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Report user: /report [reason]"""
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        if not context.args and not update.message.reply_to_message:
            await update.message.reply_text(
                "Usage: /report [reason]\n"
                "Or reply to a message with /report"
            )
            return
        
        reason = " ".join(context.args) if context.args else "No reason provided"
        reporter = update.effective_user
        
        if update.message.reply_to_message:
            target = update.message.reply_to_message.from_user
            reported_msg = update.message.reply_to_message.text or "[Media message]"
        else:
            target = None
            reported_msg = ""
        
        # Create report message
        report_text = (
            f"🚨 *New Report*\n\n"
            f"• Chat: {update.effective_chat.title}\n"
            f"• Chat ID: `{update.effective_chat.id}`\n"
            f"• Reporter: {reporter.mention_html(reporter.first_name)}\n"
            f"• Reporter ID: `{reporter.id}`\n"
        )
        
        if target:
            report_text += f"• Reported: {target.mention_html(target.first_name)}\n"
            report_text += f"• Reported ID: `{target.id}`\n"
        
        report_text += f"• Reason: {reason}\n"
        
        if reported_msg:
            report_text += f"• Message: {reported_msg[:200]}..."
        
        # Send to admins
        admins = await update.effective_chat.get_administrators()
        for admin in admins:
            try:
                if admin.user.id != reporter.id:  # Don't send to reporter
                    await context.bot.send_message(
                        chat_id=admin.user.id,
                        text=report_text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
            except:
                pass
        
        await update.message.reply_text(
            "✅ Report sent to admins!",
            reply_to_message_id=update.message.message_id
        )
    
    async def chat_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show chat settings: /settings"""
        if update.effective_chat.type == "private":
            await update.message.reply_text(config.Messages.NOT_IN_GROUP)
            return
        
        chat_id = update.effective_chat.id
        chat = data.get_chat(chat_id)
        
        response = f"⚙️ *Chat Settings for {update.effective_chat.title}:*\n\n"
        
        # Welcome settings
        welcome_enabled = "✅" if chat.get('welcome_enabled') else "❌"
        welcome_set = "✅" if chat.get('welcome') else "❌"
        response += f"Welcome: {welcome_enabled} (Set: {welcome_set})\n"
        
        # Goodbye settings
        goodbye_enabled = "✅" if chat.get('goodbye_enabled') else "❌"
        goodbye_set = "✅" if chat.get('goodbye') else "❌"
        response += f"Goodbye: {goodbye_enabled} (Set: {goodbye_set})\n"
        
        # Lock settings
        if chat.get('is_locked'):
            response += "Locks: 🔒 Fully locked\n"
        else:
            lock_types = chat.get('lock_types', [])
            if lock_types:
                response += f"Locks: 🔐 {len(lock_types)} types\n"
            else:
                response += "Locks: 🔓 No locks\n"
        
        # Rules
        rules_set = "✅" if chat.get('rules') else "❌"
        response += f"Rules: {rules_set}\n"
        
        # Filters & Notes
        filters_count = len(data.get_chat_filters(chat_id))
        notes_count = len(data.get_chat_notes(chat_id))
        response += f"Filters: {filters_count}\n"
        response += f"Notes: {notes_count}\n"
        
        response += "\nUse commands like /setwelcome, /lock, etc. to change settings."
        
        await update.message.reply_text(response, parse_mode='Markdown')

# Helper functions
def is_owner(user_id: int) -> bool:
    """Check if user is owner"""
    return user_id == config.Config.OWNER_ID

def is_sudo(user_id: int) -> bool:
    """Check if user is sudo"""
    return user_id in config.Config.SUDO_USERS or is_owner(user_id)

def extract_user_id(text: str) -> Optional[int]:
    """Extract user ID from text"""
    if not text:
        return None
    
    # Check if it's a numeric ID
    match = re.match(r'^(\d+)$', text)
    if match:
        return int(match.group(1))
    
    # Check if it's a mention
    match = re.match(r'^@(\w+)$', text)
    if match:
        # In real implementation, resolve username to ID
        return None
    
    return None

def format_time(seconds: int) -> str:
    """Format seconds to human readable time"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds//60}m"
    elif seconds < 86400:
        return f"{seconds//3600}h"
    else:
        return f"{seconds//86400}d"

def parse_time(time_str: str) -> Optional[int]:
    """Parse time string to seconds"""
    if not time_str:
        return None
    
    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }
    
    match = re.match(r'^(\d+)([smhd])$', time_str.lower())
    if match:
        value, unit = match.groups()
        return int(value) * multipliers.get(unit, 1)
    
    return None
