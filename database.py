import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import config

class DataManager:
    """JSON-based data storage manager"""
    
    def __init__(self):
        self.data_dir = config.Config.DATA_DIR
        self._ensure_data_dir()
        
        # Initialize data structures
        self.users = self._load_json("users.json", {})
        self.chats = self._load_json("chats.json", {})
        self.filters = self._load_json("filters.json", {})
        self.notes = self._load_json("notes.json", {})
        self.warns = self._load_json("warns.json", {})
        self.gbans = self._load_json("gbans.json", {})
        self.feds = self._load_json("feds.json", {})
        self.connections = self._load_json("connections.json", {})
    
    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _load_json(self, filename: str, default=None):
        """Load JSON data from file"""
        filepath = os.path.join(self.data_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return default if default is not None else {}
        return default if default is not None else {}
    
    def _save_json(self, filename: str, data):
        """Save data to JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    # ===== USER MANAGEMENT =====
    def get_user(self, user_id: int) -> Dict:
        """Get user data or create if not exists"""
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = {
                'id': int(user_id),
                'first_name': '',
                'last_name': '',
                'username': '',
                'is_banned': False,
                'is_gbanned': False,
                'warns': 0,
                'sudo': False,
                'join_date': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat()
            }
            self.save_users()
        return self.users[user_id]
    
    def update_user(self, user_id: int, **kwargs):
        """Update user data"""
        user = self.get_user(user_id)
        user.update(kwargs)
        user['last_seen'] = datetime.now().isoformat()
        self.save_users()
    
    def save_users(self):
        """Save users to file"""
        self._save_json("users.json", self.users)
    
    # ===== CHAT MANAGEMENT =====
    def get_chat(self, chat_id: int) -> Dict:
        """Get chat data or create if not exists"""
        chat_id = str(chat_id)
        if chat_id not in self.chats:
            self.chats[chat_id] = {
                'id': int(chat_id),
                'title': '',
                'welcome': '',
                'goodbye': '',
                'rules': '',
                'welcome_enabled': True,
                'goodbye_enabled': True,
                'is_locked': False,
                'lock_types': [],
                'clean_welcome': False,
                'clean_goodbye': False,
                'clean_service': True,
                'antispam': True,
                'created_at': datetime.now().isoformat()
            }
            self.save_chats()
        return self.chats[chat_id]
    
    def update_chat(self, chat_id: int, **kwargs):
        """Update chat data"""
        chat = self.get_chat(chat_id)
        chat.update(kwargs)
        self.save_chats()
    
    def save_chats(self):
        """Save chats to file"""
        self._save_json("chats.json", self.chats)
    
    # ===== FILTERS =====
    def add_filter(self, chat_id: int, keyword: str, content: str, **kwargs):
        """Add a filter"""
        chat_id = str(chat_id)
        if chat_id not in self.filters:
            self.filters[chat_id] = {}
        
        self.filters[chat_id][keyword.lower()] = {
            'content': content,
            'added_by': kwargs.get('user_id'),
            'added_at': datetime.now().isoformat(),
            **kwargs
        }
        self.save_filters()
    
    def remove_filter(self, chat_id: int, keyword: str) -> bool:
        """Remove a filter"""
        chat_id = str(chat_id)
        keyword = keyword.lower()
        
        if chat_id in self.filters and keyword in self.filters[chat_id]:
            del self.filters[chat_id][keyword]
            self.save_filters()
            return True
        return False
    
    def get_filter(self, chat_id: int, keyword: str) -> Optional[Dict]:
        """Get filter by keyword"""
        chat_id = str(chat_id)
        keyword = keyword.lower()
        
        if chat_id in self.filters:
            return self.filters[chat_id].get(keyword)
        return None
    
    def get_chat_filters(self, chat_id: int) -> Dict:
        """Get all filters for a chat"""
        chat_id = str(chat_id)
        return self.filters.get(chat_id, {})
    
    def save_filters(self):
        """Save filters to file"""
        self._save_json("filters.json", self.filters)
    
    # ===== NOTES =====
    def add_note(self, chat_id: int, name: str, content: str, **kwargs):
        """Add a note"""
        chat_id = str(chat_id)
        if chat_id not in self.notes:
            self.notes[chat_id] = {}
        
        self.notes[chat_id][name.lower()] = {
            'content': content,
            'added_by': kwargs.get('user_id'),
            'added_at': datetime.now().isoformat(),
            **kwargs
        }
        self.save_notes()
    
    def remove_note(self, chat_id: int, name: str) -> bool:
        """Remove a note"""
        chat_id = str(chat_id)
        name = name.lower()
        
        if chat_id in self.notes and name in self.notes[chat_id]:
            del self.notes[chat_id][name]
            self.save_notes()
            return True
        return False
    
    def get_note(self, chat_id: int, name: str) -> Optional[Dict]:
        """Get note by name"""
        chat_id = str(chat_id)
        name = name.lower()
        
        if chat_id in self.notes:
            return self.notes[chat_id].get(name)
        return None
    
    def get_chat_notes(self, chat_id: int) -> Dict:
        """Get all notes for a chat"""
        chat_id = str(chat_id)
        return self.notes.get(chat_id, {})
    
    def save_notes(self):
        """Save notes to file"""
        self._save_json("notes.json", self.notes)
    
    # ===== WARNS =====
    def add_warn(self, user_id: int, chat_id: int, reason: str = "", warned_by: int = 0):
        """Add a warning"""
        warn_id = f"{user_id}_{chat_id}_{datetime.now().timestamp()}"
        
        if str(chat_id) not in self.warns:
            self.warns[str(chat_id)] = {}
        
        self.warns[str(chat_id)][warn_id] = {
            'user_id': user_id,
            'reason': reason,
            'warned_by': warned_by,
            'warned_at': datetime.now().isoformat()
        }
        self.save_warns()
        
        # Update user warn count
        user = self.get_user(user_id)
        user['warns'] = user.get('warns', 0) + 1
        self.save_users()
        
        return warn_id
    
    def remove_warn(self, warn_id: str, chat_id: int) -> bool:
        """Remove a warning"""
        chat_id = str(chat_id)
        if chat_id in self.warns and warn_id in self.warns[chat_id]:
            user_id = self.warns[chat_id][warn_id]['user_id']
            del self.warns[chat_id][warn_id]
            self.save_warns()
            
            # Update user warn count
            user = self.get_user(user_id)
            user['warns'] = max(0, user.get('warns', 0) - 1)
            self.save_users()
            
            return True
        return False
    
    def get_user_warns(self, user_id: int, chat_id: int) -> List[Dict]:
        """Get all warns for a user in a chat"""
        chat_id = str(chat_id)
        user_warns = []
        
        if chat_id in self.warns:
            for warn_id, warn_data in self.warns[chat_id].items():
                if warn_data['user_id'] == user_id:
                    user_warns.append({'id': warn_id, **warn_data})
        
        return user_warns
    
    def save_warns(self):
        """Save warns to file"""
        self._save_json("warns.json", self.warns)
    
    # ===== GLOBAL BANS =====
    def add_gban(self, user_id: int, reason: str = "", banned_by: int = 0):
        """Add global ban"""
        user_id = str(user_id)
        self.gbans[user_id] = {
            'reason': reason,
            'banned_by': banned_by,
            'banned_at': datetime.now().isoformat()
        }
        
        # Update user
        user = self.get_user(int(user_id))
        user['is_gbanned'] = True
        self.save_users()
        
        self.save_gbans()
    
    def remove_gban(self, user_id: int) -> bool:
        """Remove global ban"""
        user_id = str(user_id)
        if user_id in self.gbans:
            del self.gbans[user_id]
            
            # Update user
            user = self.get_user(int(user_id))
            user['is_gbanned'] = False
            self.save_users()
            
            self.save_gbans()
            return True
        return False
    
    def is_gbanned(self, user_id: int) -> bool:
        """Check if user is globally banned"""
        return str(user_id) in self.gbans
    
    def get_gban(self, user_id: int) -> Optional[Dict]:
        """Get global ban info"""
        return self.gbans.get(str(user_id))
    
    def save_gbans(self):
        """Save global bans to file"""
        self._save_json("gbans.json", self.gbans)
    
    # ===== FEDERATIONS =====
    def create_fed(self, name: str, owner_id: int) -> str:
        """Create a new federation"""
        fed_id = f"fed_{hash(name) % 1000000}"
        
        self.feds[fed_id] = {
            'name': name,
            'owner_id': owner_id,
            'admins': [],
            'chats': [],
            'fbans': {},
            'created_at': datetime.now().isoformat()
        }
        self.save_feds()
        return fed_id
    
    def delete_fed(self, fed_id: str, owner_id: int) -> bool:
        """Delete a federation"""
        if fed_id in self.feds and self.feds[fed_id]['owner_id'] == owner_id:
            del self.feds[fed_id]
            self.save_feds()
            return True
        return False
    
    def add_fed_admin(self, fed_id: str, user_id: int, promoter_id: int) -> bool:
        """Add federation admin"""
        if fed_id in self.feds and self.feds[fed_id]['owner_id'] == promoter_id:
            if user_id not in self.feds[fed_id]['admins']:
                self.feds[fed_id]['admins'].append(user_id)
                self.save_feds()
            return True
        return False
    
    def add_fban(self, fed_id: str, user_id: int, reason: str = "", banned_by: int = 0):
        """Add federation ban"""
        if fed_id in self.feds:
            user_id = str(user_id)
            self.feds[fed_id]['fbans'][user_id] = {
                'reason': reason,
                'banned_by': banned_by,
                'banned_at': datetime.now().isoformat()
            }
            self.save_feds()
    
    def save_feds(self):
        """Save federations to file"""
        self._save_json("feds.json", self.feds)
    
    # ===== CONNECTIONS =====
    def add_connection(self, user_id: int, chat_id: int, chat_title: str = ""):
        """Add a connection"""
        user_id = str(user_id)
        if user_id not in self.connections:
            self.connections[user_id] = []
        
        # Remove existing connection to same chat
        self.connections[user_id] = [c for c in self.connections[user_id] if c['chat_id'] != chat_id]
        
        # Add new connection
        self.connections[user_id].append({
            'chat_id': chat_id,
            'chat_title': chat_title,
            'connected_at': datetime.now().isoformat()
        })
        
        # Keep only last 5 connections
        if len(self.connections[user_id]) > 5:
            self.connections[user_id] = self.connections[user_id][-5:]
        
        self.save_connections()
    
    def remove_connection(self, user_id: int, chat_id: int = 0) -> bool:
        """Remove a connection"""
        user_id = str(user_id)
        if user_id in self.connections:
            if chat_id == 0:
                # Remove all connections
                del self.connections[user_id]
            else:
                # Remove specific connection
                self.connections[user_id] = [
                    c for c in self.connections[user_id] 
                    if c['chat_id'] != chat_id
                ]
                if not self.connections[user_id]:
                    del self.connections[user_id]
            
            self.save_connections()
            return True
        return False
    
    def get_connections(self, user_id: int) -> List[Dict]:
        """Get user connections"""
        return self.connections.get(str(user_id), [])
    
    def save_connections(self):
        """Save connections to file"""
        self._save_json("connections.json", self.connections)
    
    # ===== UTILITY =====
    def get_all_sudo_users(self) -> List[int]:
        """Get all sudo users"""
        sudo_users = []
        for user_id, user_data in self.users.items():
            if user_data.get('sudo'):
                sudo_users.append(int(user_id))
        return sudo_users
    
    def cleanup(self):
        """Save all data to files"""
        self.save_users()
        self.save_chats()
        self.save_filters()
        self.save_notes()
        self.save_warns()
        self.save_gbans()
        self.save_feds()
        self.save_connections()

# Global data manager instance
data = DataManager()
