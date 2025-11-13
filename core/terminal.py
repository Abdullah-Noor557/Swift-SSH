"""
Terminal emulation for SSH sessions
Handles terminal input/output and command execution
"""

import threading
import time
import queue
from typing import Optional, Callable, Dict, Any
import paramiko
from io import StringIO

class SSHTerminal:
    def __init__(self, ssh_client: paramiko.SSHClient):
        self.ssh_client = ssh_client
        self.channel: Optional[paramiko.Channel] = None
        self.connected = False
        self.output_callback: Optional[Callable] = None
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.threads = []
        self.running = False
    
    def start_terminal(self, terminal_type: str = "xterm-256color", 
                      cols: int = 80, rows: int = 24) -> bool:
        """Start terminal session with PTY allocation"""
        try:
            if self.connected:
                self.stop_terminal()
            
            # Create channel with PTY
            self.channel = self.ssh_client.invoke_shell(
                term=terminal_type,
                width=cols,
                height=rows
            )
            
            self.connected = True
            self.running = True
            
            # Start input/output threads
            self._start_threads()
            
            return True
            
        except Exception as e:
            print(f"Error starting terminal: {e}")
            return False
    
    def stop_terminal(self):
        """Stop terminal session"""
        self.running = False
        self.connected = False
        
        # Stop all threads
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1)
        
        # Close channel
        if self.channel:
            self.channel.close()
            self.channel = None
    
    def send_input(self, data: str):
        """Send input to terminal"""
        if self.connected and self.channel:
            try:
                self.channel.send(data)
            except Exception as e:
                print(f"Error sending input: {e}")
    
    def send_command(self, command: str):
        """Send a command to the terminal"""
        self.send_input(command + "\n")
    
    def get_output(self) -> Optional[str]:
        """Get available output from terminal"""
        try:
            return self.output_queue.get_nowait()
        except queue.Empty:
            return None
    
    def set_output_callback(self, callback: Callable):
        """Set callback for terminal output"""
        self.output_callback = callback
    
    def _start_threads(self):
        """Start input/output monitoring threads"""
        # Output monitoring thread
        output_thread = threading.Thread(target=self._monitor_output, daemon=True)
        output_thread.start()
        self.threads.append(output_thread)
        
        # Input processing thread
        input_thread = threading.Thread(target=self._process_input, daemon=True)
        input_thread.start()
        self.threads.append(input_thread)
    
    def _monitor_output(self):
        """Monitor terminal output"""
        while self.running and self.connected and self.channel:
            try:
                if self.channel.recv_ready():
                    data = self.channel.recv(1024).decode('utf-8', errors='replace')
                    if data:
                        self.output_queue.put(data)
                        if self.output_callback:
                            self.output_callback(data)
                
                time.sleep(0.01)  # Small delay to prevent high CPU usage
                
            except Exception as e:
                if self.running:
                    print(f"Error monitoring output: {e}")
                break
    
    def _process_input(self):
        """Process input queue"""
        while self.running:
            try:
                # Check for input in queue
                if not self.input_queue.empty():
                    data = self.input_queue.get(timeout=0.1)
                    self.send_input(data)
                else:
                    time.sleep(0.01)
                    
            except queue.Empty:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error processing input: {e}")
                break
    
    def resize_terminal(self, cols: int, rows: int):
        """Resize terminal window"""
        if self.connected and self.channel:
            try:
                self.channel.resize_pty(width=cols, height=rows)
            except Exception as e:
                print(f"Error resizing terminal: {e}")
    
    def is_connected(self) -> bool:
        """Check if terminal is connected"""
        return self.connected and self.channel is not None and not self.channel.closed
    
    def get_terminal_info(self) -> Dict[str, Any]:
        """Get terminal information"""
        return {
            "connected": self.is_connected(),
            "channel_open": self.channel is not None and not self.channel.closed,
            "running": self.running
        }

class TerminalManager:
    """Manages multiple terminal sessions"""
    
    def __init__(self):
        self.terminals: Dict[str, SSHTerminal] = {}
        self.terminal_counter = 0
    
    def create_terminal(self, ssh_client: paramiko.SSHClient, name: Optional[str] = None) -> str:
        """Create a new terminal session"""
        if name is None:
            self.terminal_counter += 1
            name = f"Terminal {self.terminal_counter}"
        
        terminal = SSHTerminal(ssh_client)
        self.terminals[name] = terminal
        return name
    
    def get_terminal(self, name: str) -> Optional[SSHTerminal]:
        """Get terminal by name"""
        return self.terminals.get(name)
    
    def remove_terminal(self, name: str) -> bool:
        """Remove and close terminal"""
        if name in self.terminals:
            self.terminals[name].stop_terminal()
            del self.terminals[name]
            return True
        return False
    
    def list_terminals(self) -> list:
        """Get list of terminal names"""
        return list(self.terminals.keys())
    
    def close_all_terminals(self):
        """Close all terminals"""
        for terminal in self.terminals.values():
            terminal.stop_terminal()
        self.terminals.clear()
    
    def get_terminal_count(self) -> int:
        """Get number of active terminals"""
        return len(self.terminals)
