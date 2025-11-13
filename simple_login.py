"""
Simplified login window to test password functionality
"""

import customtkinter as ctk
from tkinter import messagebox
from ui.theme import apply_theme, HackerTheme

def simple_login():
    """Simple login window for testing"""
    apply_theme()
    
    window = ctk.CTk()
    window.title("SwiftSSH - Simple Login")
    window.geometry("500x400")
    
    # Main frame
    main_frame = ctk.CTkFrame(window, fg_color=HackerTheme.BG_SECONDARY)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title
    title_label = ctk.CTkLabel(
        main_frame,
        text="SwiftSSH - Simple Login",
        font=("Consolas", 20, "bold"),
        text_color=HackerTheme.ACCENT_PRIMARY
    )
    title_label.pack(pady=20)
    
    # Host field
    host_label = ctk.CTkLabel(main_frame, text="Host/IP:", font=("Consolas", 12))
    host_label.pack(anchor="w", padx=20, pady=(10, 5))
    
    host_entry = ctk.CTkEntry(
        main_frame,
        placeholder_text="192.168.1.100",
        fg_color=HackerTheme.BG_TERTIARY,
        border_color=HackerTheme.BORDER_PRIMARY,
        width=400
    )
    host_entry.pack(padx=20, pady=(0, 10))
    
    # Username field
    user_label = ctk.CTkLabel(main_frame, text="Username:", font=("Consolas", 12))
    user_label.pack(anchor="w", padx=20, pady=(10, 5))
    
    user_entry = ctk.CTkEntry(
        main_frame,
        placeholder_text="ubuntu",
        fg_color=HackerTheme.BG_TERTIARY,
        border_color=HackerTheme.BORDER_PRIMARY,
        width=400
    )
    user_entry.pack(padx=20, pady=(0, 10))
    
    # Password field
    pass_label = ctk.CTkLabel(main_frame, text="Password:", font=("Consolas", 12))
    pass_label.pack(anchor="w", padx=20, pady=(10, 5))
    
    password_entry = ctk.CTkEntry(
        main_frame,
        placeholder_text="Enter password",
        show="*",
        fg_color=HackerTheme.BG_TERTIARY,
        border_color=HackerTheme.BORDER_PRIMARY,
        width=400
    )
    password_entry.pack(padx=20, pady=(0, 20))
    
    # Connect button
    def connect():
        host = host_entry.get()
        user = user_entry.get()
        password = password_entry.get()
        
        print(f"Host: {host}")
        print(f"User: {user}")
        print(f"Password: {'*' * len(password) if password else 'EMPTY'}")
        
        if not all([host, user, password]):
            messagebox.showerror("Error", "Please fill all fields")
        else:
            messagebox.showinfo("Success", "Connection details captured!")
    
    connect_btn = ctk.CTkButton(
        main_frame,
        text="Connect",
        command=connect,
        width=400,
        height=40,
        fg_color=HackerTheme.ACCENT_PRIMARY,
        hover_color=HackerTheme.ACCENT_SECONDARY
    )
    connect_btn.pack(padx=20, pady=10)
    
    # Focus on password field
    password_entry.focus_set()
    
    window.mainloop()

if __name__ == "__main__":
    simple_login()
