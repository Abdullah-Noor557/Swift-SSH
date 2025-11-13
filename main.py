"""
SwiftSSH - Lightweight SSH GUI Client
Main entry point for the application
"""

import sys
import os
import customtkinter as ctk
from ui.login_window_fixed import LoginWindow
from ui.main_window import MainWindow
from ui.theme import apply_theme

def main():
    """Main application entry point"""
    try:
        # Apply theme globally
        apply_theme()
        
        # Create login window
        def on_connect(ssh_manager, host, username, port):
            """Handle successful connection"""
            # Create and run main window
            main_window = MainWindow(ssh_manager, host, username, port)
            main_window.run()
        
        # Create login window
        login_window = LoginWindow(on_connect_callback=on_connect)
        login_window.run()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
