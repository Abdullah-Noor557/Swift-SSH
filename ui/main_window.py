"""
Main application window
Contains file browser and terminal panels
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Optional
from core.ssh_manager import SSHManager
from core.scp_manager import SCPManager
from core.terminal import TerminalManager
from ui.theme import ModernTheme, apply_theme, get_button_style, get_card_style, get_modern_font, get_badge_style
from ui.file_browser import FileBrowser
from ui.terminal_panel import TerminalPanel
from ui.discover_panel import DiscoverPanel
from core.ui_accelerator import optimize_window

class MainWindow:
    def __init__(self, ssh_manager: SSHManager, host: str, username: str, port: int):
        self.ssh_manager = ssh_manager
        self.host = host
        self.username = username
        self.port = port
        
        # Create SCP manager
        self.scp_manager = SCPManager(ssh_manager.client, ssh_manager.sftp)
        
        # Create terminal manager
        self.terminal_manager = TerminalManager()
        
        # Create main window
        self.window = ctk.CTk()
        self.window.title(f"SwiftSSH - {username}@{host}:{port}")
        self.window.geometry("1280x900")
        self.window.resizable(True, True)
        
        # Set minimum size for better UX
        self.window.minsize(1024, 700)
        
        # Apply theme
        apply_theme()
        
        # Optimize window for better performance
        optimize_window(self.window)
        
        # Configure window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Create UI
        self._create_ui()
        
        # Create initial terminal
        self._create_initial_terminal()
        
        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        # Add tooltips for better UX
        self._add_tooltips()
    
    def _add_tooltips(self):
        """Add tooltips to UI elements"""
        try:
            from ui.theme import create_tooltip
            create_tooltip(self.new_terminal_btn, "Create new terminal session (Ctrl+T)")
            create_tooltip(self.disconnect_btn, "Disconnect from server (Ctrl+Q)")
        except Exception:
            pass  # Tooltips are optional
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for better UX"""
        # Ctrl+T for new terminal
        self.window.bind("<Control-t>", lambda e: self._new_terminal())
        # Ctrl+Q to quit (with confirmation)
        self.window.bind("<Control-q>", lambda e: self._on_closing())
        # F5 to refresh file browser
        self.window.bind("<F5>", lambda e: self._refresh_file_browser())
        # Ctrl+1 for Terminal tab
        self.window.bind("<Control-Key-1>", lambda e: self.notebook.set("💻 Terminal"))
        # Ctrl+2 for File Browser tab
        self.window.bind("<Control-Key-2>", lambda e: self.notebook.set("📁 File Browser"))
    
    def _refresh_file_browser(self):
        """Refresh file browser from keyboard shortcut"""
        if hasattr(self, 'file_browser'):
            self.file_browser._refresh_file_list()
    
    def _create_ui(self):
        """Create the main UI layout"""
        # Configure grid weights
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
        
        # Top toolbar
        self._create_toolbar()
        
        # Main content area
        self._create_content_area()
        
        # Status bar
        self._create_status_bar()
    
    def _create_toolbar(self):
        """Create modern top toolbar with professional styling"""
        toolbar = ctk.CTkFrame(self.window, fg_color=ModernTheme.BG_CARD, height=70, corner_radius=0)
        toolbar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        toolbar.grid_propagate(False)
        
        # Left section - App branding and connection info
        left_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        left_frame.pack(side="left", padx=24, pady=12)
        
        # App icon with enhanced styling
        app_icon_container = ctk.CTkFrame(left_frame, fg_color=ModernTheme.BG_TERTIARY, corner_radius=10)
        app_icon_container.pack(side="left", padx=(0, 16))
        
        app_icon = ctk.CTkLabel(
            app_icon_container,
            text="⚡",
            font=("Segoe UI Emoji", 22),
            text_color=ModernTheme.ACCENT_PRIMARY
        )
        app_icon.pack(padx=10, pady=10)
        
        # Connection info section
        connection_info = ctk.CTkFrame(left_frame, fg_color="transparent")
        connection_info.pack(side="left")
        
        # Connection status badge
        connection_frame = ctk.CTkFrame(connection_info, fg_color=ModernTheme.ACCENT_SUCCESS, corner_radius=18, height=36)
        connection_frame.pack(anchor="w")
        
        status_indicator = ctk.CTkLabel(
            connection_frame,
            text="●",
            font=get_modern_font(14),
            text_color=ModernTheme.TEXT_PRIMARY
        )
        status_indicator.pack(side="left", padx=(14, 6), pady=8)
        
        ctk.CTkLabel(
            connection_frame,
            text="Connected",
            font=get_modern_font(10, "semibold"),
            text_color=ModernTheme.BG_PRIMARY
        ).pack(side="left", padx=(0, 4), pady=8)
        
        self.connection_label = ctk.CTkLabel(
            connection_frame,
            text=f"{self.username}@{self.host}:{self.port}",
            font=get_modern_font(11, "bold"),
            text_color=ModernTheme.BG_PRIMARY
        )
        self.connection_label.pack(side="left", padx=(4, 14), pady=8)
        
        # Right section - Action buttons
        button_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        button_frame.pack(side="right", padx=24, pady=12)
        
        primary_style = get_button_style("primary")
        danger_style = get_button_style("danger")
        
        # New terminal button with enhanced icon
        self.new_terminal_btn = ctk.CTkButton(
            button_frame,
            text="➕ New Terminal",
            command=self._new_terminal,
            width=150,
            height=42,
            font=get_modern_font(11, "semibold"),
            **primary_style
        )
        self.new_terminal_btn.pack(side="left", padx=(0, 12))
        
        # Debug dropdown menu
        ghost_style = get_button_style("ghost")
        self.debug_btn = ctk.CTkButton(
            button_frame,
            text="🐛 Debug",
            command=self._show_debug_menu,
            width=120,
            height=42,
            font=get_modern_font(11, "semibold"),
            **ghost_style
        )
        self.debug_btn.pack(side="left", padx=(0, 12))
        

        # Disconnect button with enhanced styling
        self.disconnect_btn = ctk.CTkButton(
            button_frame,
            text="🔌 Disconnect",
            command=self._disconnect,
            width=140,
            height=42,
            font=get_modern_font(11, "semibold"),
            **danger_style
        )
        self.disconnect_btn.pack(side="left")
    
    def _create_content_area(self):
        """Create main content area with modern tab interface"""
        # Main content frame with enhanced styling
        content_frame = ctk.CTkFrame(self.window, fg_color=ModernTheme.BG_PRIMARY)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        # Two-column layout: left sidebar + main workspace
        content_frame.grid_columnconfigure(0, weight=0)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Left sidebar (MobaXterm-like sessions/tools panel)
        sidebar = ctk.CTkFrame(content_frame, fg_color=ModernTheme.BG_SECONDARY, width=260, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        # Sidebar header
        sidebar_header = ctk.CTkLabel(
            sidebar,
            text="Sessions",
            font=get_modern_font(12, "bold"),
            text_color=ModernTheme.TEXT_PRIMARY
        )
        sidebar_header.pack(anchor="w", padx=16, pady=(16, 6))

        # Current session card
        session_card = ctk.CTkFrame(sidebar, fg_color=ModernTheme.BG_TERTIARY, corner_radius=10)
        session_card.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkLabel(
            session_card,
            text="Current",
            font=get_modern_font(10, "semibold"),
            text_color=ModernTheme.TEXT_MUTED
        ).pack(anchor="w", padx=12, pady=(12, 2))

        ctk.CTkLabel(
            session_card,
            text=f"{self.username}@{self.host}:{self.port}",
            font=get_modern_font(11, "bold"),
            text_color=ModernTheme.TEXT_PRIMARY
        ).pack(anchor="w", padx=12, pady=(0, 12))

        # Quick actions
        quick_actions = ctk.CTkFrame(sidebar, fg_color="transparent")
        quick_actions.pack(fill="x", padx=12, pady=(0, 12))

        qa_style = get_button_style("secondary")
        ctk.CTkButton(
            quick_actions,
            text="New Terminal",
            command=self._new_terminal,
            height=34,
            font=get_modern_font(10, "semibold"),
            **qa_style
        ).pack(fill="x", pady=(0, 8))

        ctk.CTkButton(
            quick_actions,
            text="Discover SSH",
            command=lambda: self.notebook.set("🔎 Discover"),
            height=34,
            font=get_modern_font(10, "semibold"),
            **qa_style
        ).pack(fill="x")
        
        # Create modern notebook with enhanced custom styling
        self.notebook = ctk.CTkTabview(
            content_frame,
            fg_color=ModernTheme.BG_CARD,
            segmented_button_fg_color=ModernTheme.BG_SECONDARY,
            segmented_button_selected_color=ModernTheme.ACCENT_PRIMARY,
            segmented_button_selected_hover_color=ModernTheme.ACCENT_HIGHLIGHT,
            segmented_button_unselected_color=ModernTheme.BG_SECONDARY,
            segmented_button_unselected_hover_color=ModernTheme.BG_HOVER,
            text_color=ModernTheme.TEXT_PRIMARY,
            text_color_disabled=ModernTheme.TEXT_MUTED,
            corner_radius=0
        )
        self.notebook.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        # Terminal tab with icon (placed first for better UX)
        self.terminal_tab = self.notebook.add("💻 Terminal")
        self.terminal_panel = TerminalPanel(
            self.terminal_tab,
            self.ssh_manager,
            self.terminal_manager
        )
        
        # File browser tab with icon
        self.file_browser_tab = self.notebook.add("📁 File Browser")
        self.file_browser = FileBrowser(
            self.file_browser_tab,
            self.ssh_manager,
            self.scp_manager,
            self._on_file_operation
        )
        
        # Discover tab
        self.discover_tab = self.notebook.add("🔎 Discover")
        self.discover_panel = DiscoverPanel(
            self.discover_tab,
            status_callback=self._update_status
        )
        
        # Set initial tab to Terminal (more common use case)
        self.notebook.set("💻 Terminal")
    
    def _create_status_bar(self):
        """Create modern bottom status bar with enhanced styling"""
        status_frame = ctk.CTkFrame(self.window, fg_color=ModernTheme.BG_CARD, height=42, corner_radius=0)
        status_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        status_frame.grid_propagate(False)
        
        # Left status section with icon
        left_status = ctk.CTkFrame(status_frame, fg_color="transparent")
        left_status.pack(side="left", padx=24, pady=8)
        
        self.status_icon = ctk.CTkLabel(
            left_status,
            text="✓",
            font=get_modern_font(12, "bold"),
            text_color=ModernTheme.STATUS_CONNECTED
        )
        self.status_icon.pack(side="left", padx=(0, 8))
        
        self.status_label = ctk.CTkLabel(
            left_status,
            text="Ready",
            font=get_modern_font(10),
            text_color=ModernTheme.TEXT_SECONDARY
        )
        self.status_label.pack(side="left")
        
        # Middle section - Quick stats
        middle_status = ctk.CTkFrame(status_frame, fg_color="transparent")
        middle_status.pack(side="left", expand=True)
        
        # Right status section with enhanced badges
        right_status = ctk.CTkFrame(status_frame, fg_color="transparent")
        right_status.pack(side="right", padx=24, pady=8)
        
        # Terminal count badge with enhanced styling
        terminal_badge = ctk.CTkFrame(right_status, fg_color=ModernTheme.BG_TERTIARY, corner_radius=14)
        terminal_badge.pack(side="left", padx=(0, 10))
        
        terminal_icon = ctk.CTkLabel(
            terminal_badge,
            text="💻",
            font=("Segoe UI Emoji", 11)
        )
        terminal_icon.pack(side="left", padx=(10, 6), pady=6)
        
        self.terminal_count_label = ctk.CTkLabel(
            terminal_badge,
            text="1",
            font=get_modern_font(10, "semibold"),
            text_color=ModernTheme.TEXT_PRIMARY
        )
        self.terminal_count_label.pack(side="left")
        
        ctk.CTkLabel(
            terminal_badge,
            text="terminal",
            font=get_modern_font(9),
            text_color=ModernTheme.TEXT_MUTED
        ).pack(side="left", padx=(4, 10), pady=6)
        
        # Connection uptime badge
        uptime_badge = ctk.CTkFrame(right_status, fg_color=ModernTheme.BG_TERTIARY, corner_radius=14)
        uptime_badge.pack(side="left")
        
        ctk.CTkLabel(
            uptime_badge,
            text="🕐",
            font=("Segoe UI Emoji", 11)
        ).pack(side="left", padx=(10, 6), pady=6)
        
        self.uptime_label = ctk.CTkLabel(
            uptime_badge,
            text="Connected",
            font=get_modern_font(9),
            text_color=ModernTheme.TEXT_MUTED
        )
        self.uptime_label.pack(side="left", padx=(0, 10), pady=6)
    
    def _create_initial_terminal(self):
        """Create initial terminal session"""
        terminal_name = self.terminal_manager.create_terminal(self.ssh_manager.client)
        self.terminal_panel.add_terminal(terminal_name)
        self._update_terminal_count()
    
    def _new_terminal(self):
        """Create new terminal session"""
        terminal_name = self.terminal_manager.create_terminal(self.ssh_manager.client)
        self.terminal_panel.add_terminal(terminal_name)
        self._update_terminal_count()
        
        # Switch to terminal tab
        self.notebook.set("💻 Terminal")
        
        self._update_status(f"Created new terminal: {terminal_name}")

    
    
    def _disconnect(self):
        """Disconnect from SSH server"""
        if messagebox.askyesno("Disconnect", "Are you sure you want to disconnect?"):
            # Close all terminals
            self.terminal_manager.close_all_terminals()
            
            # Disconnect SSH
            self.ssh_manager.disconnect()
            
            # Close main window
            self.window.destroy()
    
    def _on_file_operation(self, operation: str, details: str):
        """Handle file operation callbacks"""
        # Determine status type based on operation
        status_type = "info"
        if "completed" in details.lower() or "success" in details.lower():
            status_type = "success"
        elif "error" in details.lower() or "failed" in details.lower():
            status_type = "error"
        elif "progress" in details.lower() or "%" in details:
            status_type = "loading"
        
        self._update_status(f"{operation}: {details}", status_type)
    
    def _update_status(self, message: str, status_type: str = "info"):
        """Update status bar with icon and color"""
        self.status_label.configure(text=message)
        
        # Update status icon based on type
        status_icons = {
            "info": "ℹ",
            "success": "✓",
            "warning": "⚠",
            "error": "✗",
            "loading": "⏳"
        }
        
        status_colors = {
            "info": ModernTheme.TEXT_INFO,
            "success": ModernTheme.STATUS_CONNECTED,
            "warning": ModernTheme.STATUS_WARNING,
            "error": ModernTheme.STATUS_DISCONNECTED,
            "loading": ModernTheme.STATUS_CONNECTING
        }
        
        icon = status_icons.get(status_type, "●")
        color = status_colors.get(status_type, ModernTheme.TEXT_SECONDARY)
        
        self.status_icon.configure(text=icon, text_color=color)
        self.status_label.configure(text_color=color)
    
    def _update_terminal_count(self):
        """Update terminal count in status bar"""
        count = self.terminal_manager.get_terminal_count()
        self.terminal_count_label.configure(text=f"{count}")
    
    def _show_debug_menu(self):
        """Show debug dropdown menu"""
        # Create popup menu
        debug_menu = ctk.CTkToplevel(self.window)
        debug_menu.title("Debug Menu")
        debug_menu.geometry("300x200")
        debug_menu.attributes("-topmost", True)
        debug_menu.resizable(False, False)
        
        # Position menu below debug button
        x = self.debug_btn.winfo_rootx()
        y = self.debug_btn.winfo_rooty() + self.debug_btn.winfo_height() + 5
        debug_menu.geometry(f"+{x}+{y}")
        
        # Menu content frame
        menu_frame = ctk.CTkFrame(debug_menu, fg_color=ModernTheme.BG_CARD)
        menu_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(
            menu_frame,
            text="Debug Tools",
            font=get_modern_font(14, "bold"),
            text_color=ModernTheme.TEXT_PRIMARY
        )
        title_label.pack(pady=(10, 20))
        
        # Demo App button
        primary_style = get_button_style("primary")
        demo_btn = ctk.CTkButton(
            menu_frame,
            text="🎭 Launch Demo Mode",
            command=lambda: [debug_menu.destroy(), self._launch_demo_app()],
            height=40,
            font=get_modern_font(11, "semibold"),
            **primary_style
        )
        demo_btn.pack(fill="x", padx=20, pady=5)
        
        # Performance stats button
        secondary_style = get_button_style("secondary")
        stats_btn = ctk.CTkButton(
            menu_frame,
            text="📊 Performance Stats",
            command=lambda: [debug_menu.destroy(), self._show_performance_stats()],
            height=40,
            font=get_modern_font(11, "semibold"),
            **secondary_style
        )
        stats_btn.pack(fill="x", padx=20, pady=5)
        
        # Close button
        ghost_style = get_button_style("ghost")
        close_btn = ctk.CTkButton(
            menu_frame,
            text="Close",
            command=debug_menu.destroy,
            height=30,
            font=get_modern_font(10, "semibold"),
            **ghost_style
        )
        close_btn.pack(fill="x", padx=20, pady=(15, 10))
        
        # Make menu modal
        debug_menu.transient(self.window)
        debug_menu.grab_set()
    
    def _launch_demo_app(self):
        """Launch the app in demo mode with mock SSH"""
        messagebox.showinfo(
            "Demo Mode",
            "Demo mode is available from the login screen.\n\n"
            "Please restart the application and use the Debug menu on the login window."
        )
    
    def _show_performance_stats(self):
        """Show performance statistics"""
        from core.ui_accelerator import get_accelerator
        
        # Calculate stats
        terminal_count = self.terminal_manager.get_terminal_count()
        accelerator = get_accelerator()
        accel_status = accelerator.get_optimization_status()
        
        # Format acceleration status
        dpi_status = "✓" if accel_status.get("dpi_awareness") else "✗"
        priority_status = "✓" if accel_status.get("process_priority") else "✗"
        
        stats_text = f"""Performance Statistics:
        
Active Terminals: {terminal_count}
Connection: {self.username}@{self.host}:{self.port}
Status: Connected

UI Optimizations:
✓ Font caching enabled
✓ Style caching enabled
✓ Terminal output batching (50ms)
✓ ANSI regex pre-compilation

Graphics Acceleration:
{dpi_status} DPI awareness (high-DPI displays)
{priority_status} Process priority optimization
✓ Window compositing enabled
✓ Double buffering enabled

Platform: {accel_status.get("platform", "Unknown")}
Memory: ~{len(self.window.winfo_children())} widgets
"""
        
        messagebox.showinfo("Performance Statistics", stats_text)
    
    def _on_closing(self):
        """Handle window closing"""
        if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
            self._disconnect()
    
    def run(self):
        """Run the main window"""
        self.window.mainloop()
