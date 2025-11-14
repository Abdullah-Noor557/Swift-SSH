"""
Mock SSH Manager for demo/debug mode
Simulates SSH connection without actual network connection
"""

import time
import threading
from typing import Optional, Callable, List, Dict, Any
import random


class MockSSHClient:
    """Mock SSH client that simulates paramiko SSHClient"""
    def __init__(self):
        self.connected = True
    
    def close(self):
        self.connected = False
    
    def exec_command(self, command: str):
        """Simulate command execution"""
        # Mock stdout, stderr, stdin
        class MockChannel:
            def __init__(self, output: str):
                self.output = output
                self.position = 0
            
            def read(self, size=1024):
                if self.position >= len(self.output):
                    return b''
                chunk = self.output[self.position:self.position+size].encode('utf-8')
                self.position += size
                return chunk
            
            def readlines(self):
                return [line.encode('utf-8') for line in self.output.split('\n')]
            
            def recv(self, size):
                return self.read(size)
        
        # Simulate command output
        if command.startswith('ls'):
            output = "file1.txt\nfile2.py\nfolder1\nfolder2\n"
        elif command.startswith('pwd'):
            output = "/home/demo\n"
        elif command.startswith('whoami'):
            output = "demo_user\n"
        elif command.startswith('uname'):
            output = "Linux demo-server 5.15.0 x86_64\n"
        elif command.startswith('echo'):
            output = command.replace('echo ', '') + "\n"
        else:
            output = f"Command executed: {command}\n"
        
        stdin = MockChannel("")
        stdout = MockChannel(output)
        stderr = MockChannel("")
        
        return stdin, stdout, stderr


class MockSFTPClient:
    """Mock SFTP client that simulates paramiko SFTPClient"""
    def __init__(self):
        self.connected = True
    
    def listdir_attr(self, path: str):
        """Simulate listing directory"""
        class MockStat:
            def __init__(self, filename: str, is_dir: bool = False):
                self.filename = filename
                self.st_mode = 0o040755 if is_dir else 0o100644
                self.st_size = random.randint(1024, 1024*1024) if not is_dir else 4096
                self.st_mtime = time.time() - random.randint(0, 86400*30)
                self.st_atime = time.time()
            
            def __str__(self):
                return self.filename
        
        # Simulate file listing
        files = [
            MockStat("file1.txt", False),
            MockStat("file2.py", False),
            MockStat("document.pdf", False),
            MockStat("image.png", False),
            MockStat("folder1", True),
            MockStat("folder2", True),
            MockStat("downloads", True),
        ]
        return files
    
    def stat(self, path: str):
        """Simulate file stat"""
        class MockStat:
            st_mode = 0o100644
            st_size = 12345
            st_mtime = time.time()
            st_atime = time.time()
        return MockStat()
    
    def get(self, remote_path: str, local_path: str, callback=None):
        """Simulate file download"""
        # Simulate download progress
        total_size = 1024 * 100  # 100KB
        chunk_size = 1024 * 10   # 10KB chunks
        
        for i in range(0, total_size, chunk_size):
            time.sleep(0.1)  # Simulate network delay
            if callback:
                callback(min(i + chunk_size, total_size), total_size)
    
    def put(self, local_path: str, remote_path: str, callback=None):
        """Simulate file upload"""
        # Simulate upload progress
        total_size = 1024 * 100  # 100KB
        chunk_size = 1024 * 10   # 10KB chunks
        
        for i in range(0, total_size, chunk_size):
            time.sleep(0.1)  # Simulate network delay
            if callback:
                callback(min(i + chunk_size, total_size), total_size)
    
    def mkdir(self, path: str):
        """Simulate directory creation"""
        pass
    
    def remove(self, path: str):
        """Simulate file deletion"""
        pass
    
    def rmdir(self, path: str):
        """Simulate directory deletion"""
        pass
    
    def close(self):
        self.connected = False


class MockTerminalChannel:
    """Mock terminal channel for interactive shell"""
    def __init__(self):
        self.output_callback = None
        self.running = False
        self.prompt = "demo@server:~$ "
        self.current_dir = "/home/demo"
        
    def recv(self, size: int) -> bytes:
        """Simulate receiving data"""
        if not self.running:
            return b''
        time.sleep(0.1)
        return b''
    
    def send(self, data: str):
        """Simulate sending data"""
        if self.output_callback:
            # Echo the input
            self.output_callback(data)
            
            # Process command if it's a newline
            if data.endswith('\n'):
                command = data.strip()
                self._process_command(command)
    
    def _process_command(self, command: str):
        """Process and respond to commands"""
        if not self.output_callback:
            return
        
        # Simulate command output
        if command == 'ls':
            output = "\nfile1.txt  file2.py  folder1/  folder2/\n"
        elif command == 'pwd':
            output = f"\n{self.current_dir}\n"
        elif command == 'whoami':
            output = "\ndemo_user\n"
        elif command.startswith('cd '):
            target = command[3:].strip()
            if target == '..':
                self.current_dir = '/'.join(self.current_dir.split('/')[:-1]) or '/'
            elif target.startswith('/'):
                self.current_dir = target
            else:
                self.current_dir = f"{self.current_dir}/{target}"
            output = "\n"
        elif command == 'clear':
            output = "\x1b[2J\x1b[H"
        elif command:
            output = f"\n{command}: command simulated in demo mode\n"
        else:
            output = "\n"
        
        # Send output
        self.output_callback(output)
        
        # Send new prompt
        prompt = f"{self.prompt}"
        self.output_callback(prompt)
    
    def close(self):
        self.running = False


class MockSSHManager:
    """Mock SSH Manager for demo mode"""
    def __init__(self):
        self.client = MockSSHClient()
        self.sftp = MockSFTPClient()
        self.connected = False
        self.connection_callbacks = (None, None)
    
    def set_connection_callbacks(self, on_success: Callable, on_error: Callable):
        """Set connection callbacks"""
        self.connection_callbacks = (on_success, on_error)
    
    def connect(self, host: str, username: str, password: str, port: int = 22):
        """Simulate SSH connection"""
        # Simulate connection delay
        time.sleep(1)
        
        self.connected = True
        
        # Call success callback
        if self.connection_callbacks[0]:
            self.connection_callbacks[0](True, "Connected to demo server")
    
    def disconnect(self):
        """Disconnect from SSH server"""
        if self.client:
            self.client.close()
        if self.sftp:
            self.sftp.close()
        self.connected = False
    
    def execute_command(self, command: str) -> tuple:
        """Execute command and return output"""
        if not self.connected:
            return ("", "Not connected", 1)
        
        stdin, stdout, stderr = self.client.exec_command(command)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        return (output, error, 0)
    
    def get_file_list(self, path: str) -> List[Dict]:
        """Get list of files in directory"""
        if not self.connected:
            return []
        
        try:
            import stat
            files = []
            for file_attr in self.sftp.listdir_attr(path):
                is_dir = stat.S_ISDIR(file_attr.st_mode)
                
                # Format permissions
                permissions = oct(file_attr.st_mode)[-3:]
                
                files.append({
                    "name": file_attr.filename,
                    "size": file_attr.st_size,
                    "modified": file_attr.st_mtime,
                    "permissions": permissions,
                    "is_directory": is_dir
                })
            
            return files
        except Exception as e:
            return []
    
    def create_directory(self, path: str) -> bool:
        """Create directory"""
        try:
            self.sftp.mkdir(path)
            return True
        except Exception:
            return False
    
    def delete_file(self, path: str) -> bool:
        """Delete file"""
        try:
            self.sftp.remove(path)
            return True
        except Exception:
            return False
    
    def delete_directory(self, path: str) -> bool:
        """Delete directory"""
        try:
            self.sftp.rmdir(path)
            return True
        except Exception:
            return False
    
    def get_file_info(self, path: str) -> Optional[Dict]:
        """Get file information"""
        try:
            file_attr = self.sftp.stat(path)
            return {
                "name": path.split('/')[-1],
                "size": file_attr.st_size,
                "modified": file_attr.st_mtime,
                "permissions": oct(file_attr.st_mode)[-3:]
            }
        except Exception:
            return None
    
    def create_shell_channel(self):
        """Create interactive shell channel"""
        return MockTerminalChannel()

