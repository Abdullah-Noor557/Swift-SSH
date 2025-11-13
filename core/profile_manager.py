"""
Encrypted profile storage system for SSH connection profiles
Uses AES encryption to securely store passwords
"""

import json
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Dict, List, Optional

class ProfileManager:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.profiles_file = os.path.join(config_dir, "profiles.enc")
        self.key_file = os.path.join(config_dir, "key.enc")
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        # Initialize encryption key
        self._init_encryption_key()
    
    def _init_encryption_key(self):
        """Initialize or load encryption key"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                self.key = f.read()
        else:
            # Generate new key
            self.key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(self.key)
        
        self.cipher = Fernet(self.key)
    
    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def save_profile(self, name: str, host: str, username: str, password: str, 
                    port: int = 22, description: str = "") -> bool:
        """Save a connection profile with encrypted password"""
        try:
            profiles = self.load_profiles()
            
            profile_data = {
                "name": name,
                "host": host,
                "username": username,
                "password": password,  # Will be encrypted
                "port": port,
                "description": description,
                "created": self._get_timestamp(),
                # Track when a profile was last used for connection
                # Note: this will be updated by mark_profile_used
                "last_used": profiles.get(name, {}).get("last_used")
            }
            
            # Encrypt the password
            encrypted_password = self.cipher.encrypt(password.encode())
            profile_data["password"] = base64.b64encode(encrypted_password).decode()
            
            profiles[name] = profile_data
            
            # Save encrypted profiles
            self._save_profiles(profiles)
            return True
            
        except Exception as e:
            print(f"Error saving profile: {e}")
            return False
    
    def load_profiles(self) -> Dict:
        """Load all profiles from encrypted storage"""
        if not os.path.exists(self.profiles_file):
            return {}
        
        try:
            with open(self.profiles_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            print(f"Error loading profiles: {e}")
            return {}
    
    def get_profile(self, name: str) -> Optional[Dict]:
        """Get a specific profile with decrypted password"""
        profiles = self.load_profiles()
        if name not in profiles:
            return None
        
        profile = profiles[name].copy()
        
        try:
            # Decrypt password
            encrypted_password = base64.b64decode(profile["password"])
            decrypted_password = self.cipher.decrypt(encrypted_password)
            profile["password"] = decrypted_password.decode()
            return profile
        except Exception as e:
            print(f"Error decrypting password for profile {name}: {e}")
            return None
    
    def delete_profile(self, name: str) -> bool:
        """Delete a profile"""
        try:
            profiles = self.load_profiles()
            if name in profiles:
                del profiles[name]
                self._save_profiles(profiles)
                return True
            return False
        except Exception as e:
            print(f"Error deleting profile: {e}")
            return False
    
    def list_profiles(self) -> List[str]:
        """Get list of profile names"""
        profiles = self.load_profiles()
        return list(profiles.keys())

    def list_profiles_by_recent(self) -> List[str]:
        """Return profile names sorted by most recently used (desc)."""
        profiles = self.load_profiles()
        def sort_key(item):
            name, data = item
            # Use last_used if present, else created, else empty string
            return data.get("last_used") or data.get("created") or ""
        # Sort by key descending (most recent first)
        sorted_items = sorted(profiles.items(), key=sort_key, reverse=True)
        return [name for name, _ in sorted_items]

    def get_most_recent_profile_name(self) -> Optional[str]:
        """Get the most recently used profile name, if any."""
        sorted_names = self.list_profiles_by_recent()
        return sorted_names[0] if sorted_names else None

    def mark_profile_used(self, name: str) -> bool:
        """Update the given profile's last_used timestamp."""
        try:
            profiles = self.load_profiles()
            if name not in profiles:
                return False
            profiles[name]["last_used"] = self._get_timestamp()
            self._save_profiles(profiles)
            return True
        except Exception as e:
            print(f"Error marking profile used: {e}")
            return False
    
    def _save_profiles(self, profiles: Dict):
        """Save profiles to encrypted storage"""
        json_data = json.dumps(profiles, indent=2)
        encrypted_data = self.cipher.encrypt(json_data.encode())
        
        with open(self.profiles_file, 'wb') as f:
            f.write(encrypted_data)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def export_profiles(self, export_path: str) -> bool:
        """Export profiles to a file (encrypted)"""
        try:
            profiles = self.load_profiles()
            with open(export_path, 'wb') as f:
                f.write(self.cipher.encrypt(json.dumps(profiles, indent=2).encode()))
            return True
        except Exception as e:
            print(f"Error exporting profiles: {e}")
            return False
    
    def import_profiles(self, import_path: str) -> bool:
        """Import profiles from a file"""
        try:
            with open(import_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            imported_profiles = json.loads(decrypted_data.decode())
            
            # Merge with existing profiles
            existing_profiles = self.load_profiles()
            existing_profiles.update(imported_profiles)
            self._save_profiles(existing_profiles)
            
            return True
        except Exception as e:
            print(f"Error importing profiles: {e}")
            return False
