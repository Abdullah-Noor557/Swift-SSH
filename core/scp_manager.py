"""
SCP file transfer manager for uploading and downloading files
Handles file transfers with progress tracking
"""

import os
import threading
import time
from typing import Optional, Callable, Tuple, Dict
from paramiko import SSHClient, SFTPClient
from paramiko.sftp_client import SFTPFile

class SCPManager:
    def __init__(self, ssh_client: SSHClient, sftp_client: SFTPClient):
        self.ssh_client = ssh_client
        self.sftp_client = sftp_client
        self.transfer_callback: Optional[Callable] = None
        self.active_transfers: Dict[str, Dict] = {}
    
    def read_remote_file(self, remote_path: str) -> Optional[str]:
        """Read content of a remote file"""
        try:
            with self.sftp_client.open(remote_path, 'r') as f:
                return f.read().decode('utf-8')
        except Exception as e:
            print(f"Error reading remote file: {e}")
            return None

    def write_remote_file(self, remote_path: str, content: str) -> bool:
        """Write content to a remote file"""
        try:
            with self.sftp_client.open(remote_path, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error writing to remote file: {e}")
            return False
    
    def set_transfer_callback(self, callback: Callable):
        """Set callback for transfer progress updates"""
        self.transfer_callback = callback
    
    def upload_file(self, local_path: str, remote_path: str, 
                   progress_callback: Optional[Callable] = None) -> bool:
        """Upload a file from local to remote server"""
        if not os.path.exists(local_path):
            return False
        
        try:
            file_size = os.path.getsize(local_path)
            transfer_id = f"upload_{int(time.time())}"
            
            # Initialize transfer tracking
            self.active_transfers[transfer_id] = {
                "type": "upload",
                "local_path": local_path,
                "remote_path": remote_path,
                "total_size": file_size,
                "transferred": 0,
                "start_time": time.time()
            }
            
            # Create remote directory if needed
            remote_dir = os.path.dirname(remote_path)
            if remote_dir and remote_dir != ".":
                self._ensure_remote_directory(remote_dir)
            
            # Upload file with progress tracking
            with open(local_path, 'rb') as local_file:
                with self.sftp_client.open(remote_path, 'wb') as remote_file:
                    self._transfer_with_progress(
                        local_file, remote_file, file_size, 
                        transfer_id, progress_callback
                    )
            
            # Clean up transfer tracking
            if transfer_id in self.active_transfers:
                del self.active_transfers[transfer_id]
            
            return True
            
        except Exception as e:
            print(f"Error uploading file: {e}")
            if transfer_id in self.active_transfers:
                del self.active_transfers[transfer_id]
            return False
    
    def download_file(self, remote_path: str, local_path: str,
                     progress_callback: Optional[Callable] = None) -> bool:
        """Download a file from remote to local server"""
        try:
            # Get remote file size
            remote_stat = self.sftp_client.stat(remote_path)
            file_size = remote_stat.st_size
            
            transfer_id = f"download_{int(time.time())}"
            
            # Initialize transfer tracking
            self.active_transfers[transfer_id] = {
                "type": "download",
                "local_path": local_path,
                "remote_path": remote_path,
                "total_size": file_size,
                "transferred": 0,
                "start_time": time.time()
            }
            
            # Create local directory if needed
            local_dir = os.path.dirname(local_path)
            if local_dir:
                os.makedirs(local_dir, exist_ok=True)
            
            # Download file with progress tracking
            with self.sftp_client.open(remote_path, 'rb') as remote_file:
                with open(local_path, 'wb') as local_file:
                    self._transfer_with_progress(
                        remote_file, local_file, file_size,
                        transfer_id, progress_callback
                    )
            
            # Clean up transfer tracking
            if transfer_id in self.active_transfers:
                del self.active_transfers[transfer_id]
            
            return True
            
        except Exception as e:
            print(f"Error downloading file: {e}")
            if transfer_id in self.active_transfers:
                del self.active_transfers[transfer_id]
            return False
    
    def _transfer_with_progress(self, source_file, dest_file, total_size: int,
                              transfer_id: str, progress_callback: Optional[Callable]):
        """Transfer file with progress tracking"""
        chunk_size = 8192  # 8KB chunks
        transferred = 0
        
        while transferred < total_size:
            chunk = source_file.read(chunk_size)
            if not chunk:
                break
            
            dest_file.write(chunk)
            transferred += len(chunk)
            
            # Update transfer tracking
            if transfer_id in self.active_transfers:
                self.active_transfers[transfer_id]["transferred"] = transferred
                
                # Calculate progress
                progress = (transferred / total_size) * 100
                speed = self._calculate_speed(transfer_id, transferred)
                
                # Call progress callback
                if progress_callback:
                    progress_callback(transfer_id, progress, speed, transferred, total_size)
                
                if self.transfer_callback:
                    self.transfer_callback(transfer_id, progress, speed, transferred, total_size)
    
    def _calculate_speed(self, transfer_id: str, transferred: int) -> float:
        """Calculate transfer speed in KB/s"""
        if transfer_id not in self.active_transfers:
            return 0.0
        
        transfer_info = self.active_transfers[transfer_id]
        elapsed_time = time.time() - transfer_info["start_time"]
        
        if elapsed_time > 0:
            return (transferred / 1024) / elapsed_time
        return 0.0
    
    def _ensure_remote_directory(self, remote_dir: str):
        """Ensure remote directory exists, create if needed"""
        if remote_dir == '/' or not remote_dir:
            return
        try:
            self.sftp_client.stat(remote_dir)
        except (IOError, FileNotFoundError):
            parent_dir = os.path.dirname(remote_dir)
            self._ensure_remote_directory(parent_dir)
            try:
                self.sftp_client.mkdir(remote_dir)
            except IOError as e:
                # Handle race condition where another process creates the directory
                try:
                    # Check if it's a directory now
                    if not self.sftp_client.stat(remote_dir).st_mode & 0o040000:
                        raise e
                except IOError:
                    # Re-raise if stat fails
                    raise e
    
    def get_transfer_status(self, transfer_id: str) -> Optional[Dict]:
        """Get status of an active transfer"""
        return self.active_transfers.get(transfer_id)
    
    def cancel_transfer(self, transfer_id: str) -> bool:
        """Cancel an active transfer"""
        if transfer_id in self.active_transfers:
            del self.active_transfers[transfer_id]
            return True
        return False
    
    def get_active_transfers(self) -> Dict[str, Dict]:
        """Get all active transfers"""
        return self.active_transfers.copy()
    
    def upload_directory(self, local_dir: str, remote_dir: str,
                        progress_callback: Optional[Callable] = None) -> bool:
        """Upload entire directory recursively"""
        try:
            if not os.path.exists(local_dir):
                return False
            
            # Create remote directory
            self._ensure_remote_directory(remote_dir)
            
            # Upload all files in directory
            for root, dirs, files in os.walk(local_dir):
                for file in files:
                    local_path = os.path.join(root, file)
                    # Calculate relative path
                    rel_path = os.path.relpath(local_path, local_dir)
                    remote_path = os.path.join(remote_dir, rel_path).replace('\\', '/')
                    
                    # Upload file
                    if not self.upload_file(local_path, remote_path, progress_callback):
                        return False
            
            return True
            
        except Exception as e:
            print(f"Error uploading directory: {e}")
            return False
    
    def download_directory(self, remote_dir: str, local_dir: str,
                          progress_callback: Optional[Callable] = None) -> bool:
        """Download entire directory recursively"""
        try:
            # Create local directory
            os.makedirs(local_dir, exist_ok=True)
            
            # Get all files in remote directory
            files = self.sftp_client.listdir_attr(remote_dir)
            
            for file_attr in files:
                remote_path = f"{remote_dir}/{file_attr.filename}"
                local_path = os.path.join(local_dir, file_attr.filename)
                
                if file_attr.st_mode & 0o040000:  # Directory
                    if not self.download_directory(remote_path, local_path, progress_callback):
                        return False
                else:  # File
                    if not self.download_file(remote_path, local_path, progress_callback):
                        return False
            
            return True
            
        except Exception as e:
            print(f"Error downloading directory: {e}")
            return False
