"""
Simplified login window to ensure password field works
"""

import customtkinter as ctk
from tkinter import messagebox
from ui.theme import apply_theme, HackerTheme

class SimpleLoginWindow:
    def __init__(self, on_connect_callback=None):
        self.on_connect_callback = on_connect_callback
        
        # Create main window
        self.window = ctk.CTk()
        self.window.title("SwiftSSH - Connect")
        self.window.geometry("500x600")
        self.window.resizable(False, False)
        
        # Apply theme
        apply_theme()
        
        # Create UI
        self._create_ui()
    
    def _create_ui(self):
        """Create the login UI"""
        # Main frame
        main_frame = ctk.CTkFrame(self.window, fg_color=HackerTheme.BG_SECONDARY)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="SwiftSSH",
            font=("Consolas", 24, "bold"),
            text_color=HackerTheme.ACCENT_PRIMARY
        )
        title_label.pack(pady=(20, 10))
        
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Secure Shell Client",
            font=("Consolas", 12),
            text_color=HackerTheme.TEXT_SECONDARY
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Connection form
        form_frame = ctk.CTkFrame(main_frame, fg_color=HackerTheme.BG_TERTIARY)
        form_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            form_frame,
            text="Connection Details",
            font=("Consolas", 14, "bold"),
            text_color=HackerTheme.TEXT_PRIMARY
        ).pack(pady=(15, 10))
        
        # Host field
        ctk.CTkLabel(
            form_frame,
            text="Host/IP:",
            font=("Consolas", 12),
            text_color=HackerTheme.TEXT_PRIMARY
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.host_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="192.168.1.100",
            fg_color=HackerTheme.BG_SECONDARY,
            border_color=HackerTheme.BORDER_PRIMARY
        )
        self.host_entry.pack(fill="x", padx=15, pady=(0, 10))
        
        # Username field
        ctk.CTkLabel(
            form_frame,
            text="Username:",
            font=("Consolas", 12),
            text_color=HackerTheme.TEXT_PRIMARY
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.username_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="ubuntu",
            fg_color=HackerTheme.BG_SECONDARY,
            border_color=HackerTheme.BORDER_PRIMARY
        )
        self.username_entry.pack(fill="x", padx=15, pady=(0, 10))
        
        # Password field - MAKE SURE THIS IS VISIBLE
        password_label = ctk.CTkLabel(
            form_frame,
            text="Password:",
            font=("Consolas", 12),
            text_color=HackerTheme.TEXT_PRIMARY
        )
        password_label.pack(anchor="w", padx=15, pady=(10, 5))
        
        self.password_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter password",
            show="*",
            fg_color=HackerTheme.BG_SECONDARY,
            border_color=HackerTheme.BORDER_PRIMARY
        )
        self.password_entry.pack(fill="x", padx=15, pady=(0, 10))
        
        # Port field
        ctk.CTkLabel(
            form_frame,
            text="Port:",
            font=("Consolas", 12),
            text_color=HackerTheme.TEXT_PRIMARY
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.port_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="22",
            fg_color=HackerTheme.BG_SECONDARY,
            border_color=HackerTheme.BORDER_PRIMARY
        )
        self.port_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Connect button
        self.connect_button = ctk.CTkButton(
            main_frame,
            text="Connect",
            command=self._connect,
            height=40,
            font=("Consolas", 14, "bold"),
            fg_color=HackerTheme.ACCENT_PRIMARY,
            hover_color=HackerTheme.ACCENT_SECONDARY
        )
        self.connect_button.pack(fill="x", padx=20, pady=(0, 20))
        
        # Status label
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Ready to connect",
            font=("Consolas", 10),
            text_color=HackerTheme.TEXT_MUTED
        )
        self.status_label.pack(pady=(0, 20))
        
        # Focus on password field
        self.password_entry.focus_set()
    
    def _connect(self):
        """Attempt SSH connection"""
        host = self.host_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        port = self.port_entry.get().strip()
        
        print(f"Debug: Host={host}, Username={username}, Password={'*' * len(password) if password else 'EMPTY'}")
        
        if not all([host, username, password]):
            messagebox.showerror("Error", "Please fill in all required fields")
            return
        
        try:
            port = int(port) if port else 22
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
            return
        
        # Update UI for connection attempt
        self.connect_button.configure(text="Connecting...", state="disabled")
        self._update_status("Connecting...", HackerTheme.STATUS_CONNECTING)
        
        # Simulate connection (replace with actual SSH connection)
        self.window.after(2000, self._simulate_connection)
    
    def _simulate_connection(self):
        """Simulate connection for testing"""
        self.connect_button.configure(text="Connect", state="normal")
        self._update_status("Connection simulated - password field is working!", HackerTheme.STATUS_CONNECTED)
        
        # Show success message
        messagebox.showinfo("Success", "Password field is working! You can now use the main application.")
    
    def _update_status(self, message: str, color: str = None):
        """Update status label"""
        self.status_label.configure(text=message)
        if color:
            self.status_label.configure(text_color=color)
        else:
            self.status_label.configure(text_color=HackerTheme.TEXT_MUTED)
    
    def run(self):
        """Run the login window"""
        self.window.mainloop()
    
    def destroy(self):
        """Destroy the login window"""
        if self.window:
            self.window.destroy()
