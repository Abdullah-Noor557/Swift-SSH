"""
Simple test to verify password field functionality
"""

import customtkinter as ctk
from ui.theme import apply_theme, HackerTheme

def test_password_field():
    """Test password field functionality"""
    apply_theme()
    
    window = ctk.CTk()
    window.title("Password Field Test")
    window.geometry("400x200")
    
    # Create frame
    frame = ctk.CTkFrame(window, fg_color=HackerTheme.BG_SECONDARY)
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Label
    label = ctk.CTkLabel(frame, text="Test Password Field:", font=("Consolas", 14))
    label.pack(pady=10)
    
    # Password entry
    password_entry = ctk.CTkEntry(
        frame,
        placeholder_text="Enter password here",
        show="*",
        fg_color=HackerTheme.BG_TERTIARY,
        border_color=HackerTheme.BORDER_PRIMARY,
        width=300
    )
    password_entry.pack(pady=10)
    
    # Test button
    def test_password():
        password = password_entry.get()
        print(f"Password entered: {'*' * len(password) if password else 'EMPTY'}")
        if password:
            print("✅ Password field is working!")
        else:
            print("❌ No password entered")
    
    test_btn = ctk.CTkButton(
        frame,
        text="Test Password",
        command=test_password,
        fg_color=HackerTheme.ACCENT_PRIMARY
    )
    test_btn.pack(pady=10)
    
    # Focus on password field
    password_entry.focus_set()
    
    window.mainloop()

if __name__ == "__main__":
    test_password_field()
