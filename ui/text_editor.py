"""
Modern text editor window with professional UI
"""

import customtkinter as ctk
from tkinter import messagebox
import os
from core.ssh_manager import SSHManager
from core.scp_manager import SCPManager
from ui.theme import ModernTheme, get_button_style, get_card_style, get_modern_font, get_badge_style

class TextEditorWindow(ctk.CTkToplevel):
    def __init__(self, parent, ssh_manager: SSHManager, remote_path: str):
        super().__init__(parent)
        
        # Window setup
        filename = os.path.basename(remote_path)
        self.title(f"✏ SwiftSSH Editor - {filename}")
        self.geometry("1100x750")
        self.minsize(700, 500)
        
        # Apply theme
        self.configure(fg_color=ModernTheme.BG_PRIMARY)

        self.ssh_manager = ssh_manager
        sftp_client = self.ssh_manager.client.open_sftp()
        self.scp_manager = SCPManager(self.ssh_manager.client, sftp_client)
        self.remote_path = remote_path
        self.filename = filename
        self.is_modified = False

        self._create_widgets()
        self._load_file_content()
        self._setup_keyboard_shortcuts()
        self._add_tooltips()
    
    def _add_tooltips(self):
        """Add tooltips to UI elements"""
        try:
            from ui.theme import create_tooltip
            create_tooltip(self.save_button, "Save file to server (Ctrl+S)")
            create_tooltip(self.cancel_button, "Close editor without saving (Escape)")
        except Exception:
            pass  # Tooltips are optional
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for better UX"""
        # Ctrl+S to save
        self.bind("<Control-s>", lambda e: self._save_file())
        # Escape to cancel
        self.bind("<Escape>", lambda e: self.destroy())
        # Ctrl+F to find (placeholder for future implementation)
        # self.bind("<Control-f>", lambda e: self._show_find_dialog())

    def _create_widgets(self):
        """Create modern editor UI"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header bar with file info
        self._create_header()
        
        # Editor area
        self._create_editor()
        
        # Footer with action buttons
        self._create_footer()
    
    def _create_header(self):
        """Create modern header bar with enhanced styling"""
        header = ctk.CTkFrame(self, fg_color=ModernTheme.BG_CARD, height=70, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_propagate(False)
        
        # Left section - File info with modern layout
        left_frame = ctk.CTkFrame(header, fg_color="transparent")
        left_frame.pack(side="left", padx=24, pady=14)
        
        # File icon with background
        file_ext = os.path.splitext(self.filename)[1].lower()
        icon = self._get_file_icon(file_ext)
        icon_container = ctk.CTkFrame(left_frame, fg_color=ModernTheme.BG_TERTIARY, corner_radius=10)
        icon_container.pack(side="left", padx=(0, 16))
        
        icon_label = ctk.CTkLabel(
            icon_container,
            text=icon,
            font=("Segoe UI Emoji", 26)
        )
        icon_label.pack(padx=12, pady=12)
        
        # File info with enhanced typography
        info_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        info_frame.pack(side="left")
        
        title_label = ctk.CTkLabel(
            info_frame,
            text=self.filename,
            font=get_modern_font(15, "bold"),
            text_color=ModernTheme.TEXT_PRIMARY
        )
        title_label.pack(anchor="w")
        
        path_label = ctk.CTkLabel(
            info_frame,
            text=f"📁 {self.remote_path}",
            font=get_modern_font(9),
            text_color=ModernTheme.TEXT_MUTED
        )
        path_label.pack(anchor="w", pady=(2, 0))
        
        # Right section - Status badge with enhanced styling
        self.status_badge = ctk.CTkFrame(header, fg_color=ModernTheme.BG_TERTIARY, corner_radius=18)
        self.status_badge.pack(side="right", padx=24, pady=14)
        
        self.status_label = ctk.CTkLabel(
            self.status_badge,
            text="● Unchanged",
            font=get_modern_font(10, "semibold"),
            text_color=ModernTheme.TEXT_MUTED
        )
        self.status_label.pack(padx=16, pady=8)
    
    def _create_editor(self):
        """Create text editor area with enhanced styling"""
        editor_frame = ctk.CTkFrame(self, fg_color=ModernTheme.BG_CARD, corner_radius=0)
        editor_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        editor_frame.grid_columnconfigure(0, weight=1)
        editor_frame.grid_rowconfigure(0, weight=1)
        
        # Editor with enhanced styling
        self.text_area = ctk.CTkTextbox(
            editor_frame,
            wrap="none",
            font=("Consolas", 11),
            fg_color=ModernTheme.BG_TERTIARY,
            text_color=ModernTheme.TEXT_PRIMARY,
            border_width=0,
            corner_radius=0
        )
        self.text_area.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        
        # Track modifications
        self.text_area.bind("<<Modified>>", self._on_text_modified)
        
        # Add line number indicator
        self._add_editor_info()
    
    def _add_editor_info(self):
        """Add editor info bar"""
        # This would typically show line/col, encoding, etc.
        pass
    
    def _create_footer(self):
        """Create footer with action buttons and enhanced styling"""
        footer = ctk.CTkFrame(self, fg_color=ModernTheme.BG_CARD, height=76, corner_radius=0)
        footer.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        footer.grid_propagate(False)
        
        button_frame = ctk.CTkFrame(footer, fg_color="transparent")
        button_frame.pack(expand=True, pady=16)
        
        primary_style = get_button_style("primary")
        ghost_style = get_button_style("ghost")
        
        # Save button with enhanced styling
        self.save_button = ctk.CTkButton(
            button_frame,
            text="💾 Save Changes",
            command=self._save_file,
            width=190,
            height=46,
            font=get_modern_font(13, "bold"),
            **primary_style
        )
        self.save_button.pack(side="left", padx=(0, 12))

        # Cancel button with enhanced styling
        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="✕ Cancel",
            command=self.destroy,
            width=150,
            height=46,
            font=get_modern_font(13, "bold"),
            **ghost_style
        )
        self.cancel_button.pack(side="left")
    
    def _get_file_icon(self, ext: str) -> str:
        """Get icon based on file extension"""
        icon_map = {
            '.py': '🐍', '.js': '📜', '.html': '🌐', '.css': '🎨',
            '.txt': '📄', '.md': '📝', '.json': '📋', '.xml': '📋',
            '.sh': '🔧', '.log': '📋', '.conf': '⚙', '.ini': '⚙'
        }
        return icon_map.get(ext, '📄')
    
    def _on_text_modified(self, event=None):
        """Handle text modification with enhanced visual feedback"""
        if self.text_area.edit_modified():
            self.is_modified = True
            self.status_label.configure(
                text="● Modified",
                text_color=ModernTheme.TEXT_WARNING
            )
            self.status_badge.configure(fg_color=ModernTheme.ACCENT_WARNING)
            self.text_area.edit_modified(False)

    def _load_file_content(self):
        try:
            content = self.scp_manager.read_remote_file(self.remote_path)
            if content is not None:
                self.text_area.insert("1.0", content)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {e}")
            self.destroy()

    def _save_file(self):
        """Save file with enhanced modern feedback"""
        content = self.text_area.get("1.0", "end-1c")
        try:
            # Update UI to show saving
            self.save_button.configure(text="⏳ Saving...", state="disabled")
            self.status_label.configure(
                text="● Saving...",
                text_color=ModernTheme.STATUS_CONNECTING
            )
            self.status_badge.configure(fg_color=ModernTheme.ACCENT_WARNING)
            
            if self.scp_manager.write_remote_file(self.remote_path, content):
                # Success feedback with enhanced styling
                self.is_modified = False
                self.status_label.configure(
                    text="✓ Saved",
                    text_color=ModernTheme.STATUS_CONNECTED
                )
                self.status_badge.configure(fg_color=ModernTheme.ACCENT_SUCCESS)
                
                # Show success message and close
                self.after(600, lambda: self._show_success_and_close())
            else:
                # Error feedback
                self.save_button.configure(text="💾 Save Changes", state="normal")
                self.status_label.configure(
                    text="✕ Failed",
                    text_color=ModernTheme.STATUS_DISCONNECTED
                )
                self.status_badge.configure(fg_color=ModernTheme.ACCENT_ERROR)
                messagebox.showerror("Error", "Failed to save file.")
        except Exception as e:
            self.save_button.configure(text="💾 Save Changes", state="normal")
            self.status_label.configure(
                text="✕ Error",
                text_color=ModernTheme.STATUS_DISCONNECTED
            )
            self.status_badge.configure(fg_color=ModernTheme.ACCENT_ERROR)
            messagebox.showerror("Error", f"Failed to save file: {e}")
    
    def _show_success_and_close(self):
        """Show success message and close window"""
        messagebox.showinfo("Success", f"File '{self.filename}' saved successfully!")
        self.destroy()
