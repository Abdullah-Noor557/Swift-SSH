"""
SSH connection manager using Paramiko
Handles SSH connections, authentication, and basic operations
"""

import paramiko
import threading
import time
from typing import Optional, Callable, Dict, Any
from io import StringIO

class SSHManager:
    def __init__(self):
        self.client: Optional[paramiko.SSHClient] = None
        self.sftp: Optional[paramiko.SFTPClient] = None
        self.connected = False
        self.connection_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
    
    def connect(self, host: str, username: str, password: str, port: int = 22, 
                timeout: int = 10) -> bool:
        """Establish SSH connection"""
        try:
            if self.connected:
                self.disconnect()
            
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect with timeout
            self.client.connect(
                hostname=host,
                username=username,
                password=password,
                port=port,
                timeout=timeout,
                allow_agent=False,
                look_for_keys=False
            )
            
            # Create SFTP client for file operations
            self.sftp = self.client.open_sftp()
            self.connected = True
            
            if self.connection_callback:
                self.connection_callback(True, f"Connected to {host}")
            
            return True
            
        except paramiko.AuthenticationException:
            error_msg = "Authentication failed. Check username and password."
            if self.error_callback:
                self.error_callback(error_msg)
            return False
            
        except paramiko.SSHException as e:
            error_msg = f"SSH connection error: {str(e)}"
            if self.error_callback:
                self.error_callback(error_msg)
            return False
            
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            if self.error_callback:
                self.error_callback(error_msg)
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        try:
            if self.sftp:
                self.sftp.close()
                self.sftp = None
            
            if self.client:
                self.client.close()
                self.client = None
            
            self.connected = False
            
            if self.connection_callback:
                self.connection_callback(False, "Disconnected")
                
        except Exception as e:
            print(f"Error during disconnect: {e}")
    
    def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute a command on the remote server"""
        if not self.connected or not self.client:
            return {"success": False, "error": "Not connected"}
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            
            # Read output
            stdout_data = stdout.read().decode('utf-8', errors='replace')
            stderr_data = stderr.read().decode('utf-8', errors='replace')
            exit_code = stdout.channel.recv_exit_status()
            
            return {
                "success": exit_code == 0,
                "stdout": stdout_data,
                "stderr": stderr_data,
                "exit_code": exit_code,
                "command": command
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    def get_file_list(self, remote_path: str = ".") -> list:
        """Get list of files and directories in remote path"""
        if not self.connected or not self.sftp:
            return []
        
        try:
            files = []
            for item in self.sftp.listdir_attr(remote_path):
                file_info = {
                    "name": item.filename,
                    "size": item.st_size,
                    "permissions": oct(item.st_mode)[-3:],
                    "modified": item.st_mtime,
                    "is_directory": item.st_mode & 0o040000 != 0,
                    "path": f"{remote_path}/{item.filename}" if remote_path != "." else item.filename
                }
                files.append(file_info)
            
            # Sort: directories first, then files, both alphabetically
            files.sort(key=lambda x: (not x["is_directory"], x["name"].lower()))
            return files
            
        except Exception as e:
            print(f"Error listing files: {e}")
            return []
    
    def get_file_info(self, remote_path: str) -> Optional[Dict]:
        """Get detailed information about a file"""
        if not self.connected or not self.sftp:
            return None
        
        try:
            stat = self.sftp.stat(remote_path)
            return {
                "name": remote_path.split('/')[-1],
                "size": stat.st_size,
                "permissions": oct(stat.st_mode)[-3:],
                "modified": stat.st_mtime,
                "is_directory": stat.st_mode & 0o040000 != 0,
                "path": remote_path
            }
        except Exception as e:
            print(f"Error getting file info: {e}")
            return None
    
    def create_directory(self, remote_path: str) -> bool:
        """Create a directory on remote server"""
        if not self.connected or not self.sftp:
            return False
        
        try:
            self.sftp.mkdir(remote_path)
            return True
        except Exception as e:
            print(f"Error creating directory: {e}")
            return False
    
    def delete_file(self, remote_path: str) -> bool:
        """Delete a file on remote server"""
        if not self.connected or not self.sftp:
            return False
        
        try:
            self.sftp.remove(remote_path)
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def delete_directory(self, remote_path: str) -> bool:
        """Delete a directory on remote server"""
        if not self.connected or not self.sftp:
            return False
        
        try:
            self.sftp.rmdir(remote_path)
            return True
        except Exception as e:
            print(f"Error deleting directory: {e}")
            return False
    
    def rename_file(self, old_path: str, new_path: str) -> bool:
        """Rename a file on remote server"""
        if not self.connected or not self.sftp:
            return False
        
        try:
            self.sftp.rename(old_path, new_path)
            return True
        except Exception as e:
            print(f"Error renaming file: {e}")
            return False
    
    def set_connection_callbacks(self, connection_callback: Callable = None, 
                               error_callback: Callable = None):
        """Set callback functions for connection events"""
        self.connection_callback = connection_callback
        self.error_callback = error_callback
    
    def is_connected(self) -> bool:
        """Check if SSH connection is active"""
        return self.connected and self.client is not None
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information"""
        if not self.connected:
            return {"connected": False}
        
        try:
            transport = self.client.get_transport()
            return {
                "connected": True,
                "host": transport.getpeername()[0],
                "port": transport.getpeername()[1],
                "username": transport.get_username(),
                "active": transport.is_active()
            }
        except Exception:
            return {"connected": False}
