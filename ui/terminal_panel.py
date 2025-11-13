"""
Terminal panel with tabbed interface for multiple SSH sessions
Handles terminal emulation and multiple concurrent sessions
"""

import customtkinter as ctk
from tkinter import scrolledtext, messagebox
import threading
import time
from typing import Optional, Callable, Dict
import re
from core.ssh_manager import SSHManager
from core.terminal import TerminalManager, SSHTerminal
from ui.theme import ModernTheme, get_terminal_style, get_button_style, get_modern_font
from ui.text_editor import TextEditorWindow

class TerminalPanel:
    def __init__(self, parent, ssh_manager: SSHManager, terminal_manager: TerminalManager):
        self.parent = parent
        self.ssh_manager = ssh_manager
        self.terminal_manager = terminal_manager
        self.terminals: Dict[str, SSHTerminal] = {}
        self.terminal_widgets: Dict[str, ctk.CTkFrame] = {}
        self.current_terminal = None
        self.terminal_states = {}
        self.input_buffers = {}

        self.ansi_color_map = {
            # Foreground
            30: 'black', 31: 'red', 32: 'green', 33: 'yellow', 34: 'blue', 35: 'magenta', 36: 'cyan', 37: 'white',
            39: 'default_fg',
            # Bright Foreground
            90: 'bright_black', 91: 'bright_red', 92: 'bright_green', 93: 'bright_yellow', 94: 'bright_blue', 95: 'bright_magenta', 96: 'bright_cyan', 97: 'bright_white',
            # Background
            40: 'bg_black', 41: 'bg_red', 42: 'bg_green', 43: 'bg_yellow', 44: 'bg_blue', 45: 'bg_magenta', 46: 'bg_cyan', 47: 'bg_white',
            49: 'default_bg',
            # Bright Background
            100: 'bg_bright_black', 101: 'bg_bright_red', 102: 'bg_bright_green', 103: 'bg_bright_yellow', 104: 'bg_bright_blue', 105: 'bg_bright_magenta', 106: 'bg_bright_cyan', 107: 'bg_bright_white',
            # Style
            1: 'bold', 2: 'dim', 4: 'underline', 5: 'blink', 7: 'reverse', 8: 'hidden',
            22: 'normal', 24: 'no_underline'
        }
        self.fg_colors = {k for k, v in self.ansi_color_map.items() if (30 <= k <= 37) or (90 <= k <= 97)}
        self.bg_colors = {k for k, v in self.ansi_color_map.items() if (40 <= k <= 47) or (100 <= k <= 107)}
        
        # Create UI
        self._create_ui()

        # Keyboard shortcuts for terminals
        self._setup_keyboard_shortcuts()
    
    def _create_ui(self):
        """Create the terminal panel UI"""
        # Configure parent grid to fill available space
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(0, weight=1)
        
        # Create main frame for proper layout
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # Configure grid for main frame
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Store main frame reference
        self.main_frame = main_frame
        
        # Terminal tabs
        self._create_terminal_tabs()
        
        # Terminal content area
        self._create_terminal_content()
    
    def _create_terminal_tabs(self):
        """Create modern terminal tab interface"""
        self.tab_frame = ctk.CTkFrame(self.main_frame, fg_color=ModernTheme.BG_TERTIARY, height=48, corner_radius=8)
        self.tab_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))
        self.tab_frame.grid_propagate(False)
        
        # Tab buttons will be created dynamically
        self.tab_buttons = {}
        self.tab_button_frame = ctk.CTkScrollableFrame(
            self.tab_frame,
            fg_color="transparent",
            orientation="horizontal",
            height=38
        )
        self.tab_button_frame.pack(side="left", fill="x", expand=True, padx=8, pady=5)
        
        # New terminal button with modern styling
        primary_style = get_button_style("primary")
        self.new_terminal_btn = ctk.CTkButton(
            self.tab_frame,
            text="➕",
            command=self._new_terminal,
            width=36,
            height=36,
            font=("Segoe UI", 14),
            **primary_style
        )
        self.new_terminal_btn.pack(side="right", padx=(8, 12), pady=6)
    
    def _create_terminal_content(self):
        """Create modern terminal content area"""
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color=ModernTheme.TERMINAL_BG, corner_radius=0)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 8))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
    
    def add_terminal(self, terminal_name: str):
        """Add a new terminal session"""
        # Create terminal instance
        terminal = self.terminal_manager.get_terminal(terminal_name)
        if not terminal:
            return
        
        self.input_buffers[terminal_name] = ""
        
        # Start terminal session
        if not terminal.start_terminal():
            messagebox.showerror("Error", f"Failed to start terminal: {terminal_name}")
            return
        
        # Create terminal widget
        terminal_widget = self._create_terminal_widget(terminal_name, terminal)
        self.terminals[terminal_name] = terminal
        self.terminal_widgets[terminal_name] = terminal_widget
        
        # Create tab button
        self._create_tab_button(terminal_name)
        
        # Show this terminal
        self._show_terminal(terminal_name)
    
    def _create_terminal_widget(self, terminal_name: str, terminal: SSHTerminal) -> ctk.CTkFrame:
        """Create terminal widget for a session"""
        # Terminal frame
        terminal_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Terminal text widget
        import tkinter as tk
        from tkinter import scrolledtext
        
        # Create scrolled text widget
        text_widget = scrolledtext.ScrolledText(
            terminal_frame,
            **get_terminal_style(),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configure text widget for colors
        self._configure_terminal_colors(text_widget)
        
        # Bind events
        text_widget.bind("<Key>", lambda e: self._on_key_press(terminal_name, e))
        text_widget.bind("<Button-1>", lambda e: text_widget.focus_set())
        
        # Store references
        terminal_frame.text_widget = text_widget
        terminal_frame.terminal = terminal
        self.terminal_states[terminal_name] = {'tags': set()}
        
        # Set up output callback
        terminal.set_output_callback(lambda data: self._on_terminal_output(terminal_name, data))
        
        return terminal_frame
    
    def _configure_terminal_colors(self, text_widget):
        """Configure text widget with color tags for terminal colors"""
        # Define color tags for ANSI colors
        terminal_style = get_terminal_style()
        color_tags = {
            'black': {'foreground': '#000000'},
            'red': {'foreground': '#FF0000'},
            'green': {'foreground': '#00FF00'},
            'yellow': {'foreground': '#FFFF00'},
            'blue': {'foreground': '#0000FF'},
            'magenta': {'foreground': '#FF00FF'},
            'cyan': {'foreground': '#00FFFF'},
            'white': {'foreground': '#FFFFFF'},
            'bright_black': {'foreground': '#888888'},
            'bright_red': {'foreground': '#FF6666'},
            'bright_green': {'foreground': '#66FF66'},
            'bright_yellow': {'foreground': '#FFFF66'},
            'bright_blue': {'foreground': '#6666FF'},
            'bright_magenta': {'foreground': '#FF66FF'},
            'bright_cyan': {'foreground': '#66FFFF'},
            'bright_white': {'foreground': '#FFFFFF'},
            'default_fg': {'foreground': terminal_style['fg']},

            'bg_black': {'background': '#000000'},
            'bg_red': {'background': '#FF0000'},
            'bg_green': {'background': '#00FF00'},
            'bg_yellow': {'background': '#FFFF00'},
            'bg_blue': {'background': '#0000FF'},
            'bg_magenta': {'background': '#FF00FF'},
            'bg_cyan': {'background': '#00FFFF'},
            'bg_white': {'background': '#FFFFFF'},
            'bg_bright_black': {'background': '#888888'},
            'bg_bright_red': {'background': '#FF6666'},
            'bg_bright_green': {'background': '#66FF66'},
            'bg_bright_yellow': {'background': '#FFFF66'},
            'bg_bright_blue': {'background': '#6666FF'},
            'bg_bright_magenta': {'background': '#FF66FF'},
            'bg_bright_cyan': {'background': '#66FFFF'},
            'bg_bright_white': {'background': '#FFFFFF'},
            'default_bg': {'background': terminal_style['bg']},

            'bold': {'font': (terminal_style['font'][0], terminal_style['font'][1], 'bold')},
            'dim': {'foreground': '#888888'},
            'underline': {'underline': True},
            'hidden': {'foreground': terminal_style['bg']},
        }
        
        # Configure all color tags
        for tag_name, tag_config in color_tags.items():
            text_widget.tag_configure(tag_name, **tag_config)
    
    def _create_tab_button(self, terminal_name: str):
        """Create modern tab button for terminal"""
        # Tab button frame with card-like appearance
        tab_frame = ctk.CTkFrame(
            self.tab_button_frame,
            fg_color=ModernTheme.BG_SECONDARY,
            corner_radius=8,
            border_width=2,
            border_color=ModernTheme.BORDER_SUBTLE
        )
        tab_frame.pack(side="left", padx=4, pady=2)
        
        # Terminal icon
        icon_label = ctk.CTkLabel(
            tab_frame,
            text="💻",
            font=("Segoe UI Emoji", 12)
        )
        icon_label.pack(side="left", padx=(10, 4), pady=6)
        
        # Terminal name label
        name_label = ctk.CTkLabel(
            tab_frame,
            text=terminal_name,
            font=get_modern_font(10, "semibold"),
            text_color=ModernTheme.TEXT_PRIMARY
        )
        name_label.pack(side="left", padx=(0, 8), pady=6)
        
        # Close button with modern styling
        danger_style = get_button_style("danger")
        close_btn = ctk.CTkButton(
            tab_frame,
            text="✕",
            command=lambda: self._close_terminal(terminal_name),
            width=24,
            height=24,
            font=get_modern_font(10, "bold"),
            **danger_style
        )
        close_btn.pack(side="right", padx=(0, 6), pady=6)
        
        # Click handler for tab
        def on_tab_click(event):
            self._show_terminal(terminal_name)
        
        tab_frame.bind("<Button-1>", on_tab_click)
        name_label.bind("<Button-1>", on_tab_click)
        icon_label.bind("<Button-1>", on_tab_click)
        
        # Store tab button reference
        self.tab_buttons[terminal_name] = tab_frame

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for terminal management"""
        try:
            # New terminal: Ctrl+Shift+T
            self.parent.bind("<Control-Shift-Key-T>", lambda e: self._new_terminal())
            # Close current terminal: Ctrl+W
            self.parent.bind("<Control-w>", lambda e: self._close_current_terminal())
        except Exception:
            pass

    def _close_current_terminal(self):
        """Close the currently active terminal tab"""
        if self.current_terminal:
            self._close_terminal(self.current_terminal)
    
    def _show_terminal(self, terminal_name: str):
        """Show a specific terminal"""
        if terminal_name not in self.terminal_widgets:
            return
        
        # Hide all terminals
        for widget in self.terminal_widgets.values():
            widget.grid_remove()
        
        # Show selected terminal
        self.terminal_widgets[terminal_name].grid(row=0, column=0, sticky="nsew")
        self.current_terminal = terminal_name
        
        # Update tab appearance
        self._update_tab_appearance(terminal_name)
    
    def _update_tab_appearance(self, active_terminal: str):
        """Update tab button appearance with modern styling"""
        for name, tab_frame in self.tab_buttons.items():
            if name == active_terminal:
                tab_frame.configure(
                    fg_color=ModernTheme.ACCENT_PRIMARY,
                    border_color=ModernTheme.ACCENT_PRIMARY
                )
            else:
                tab_frame.configure(
                    fg_color=ModernTheme.BG_SECONDARY,
                    border_color=ModernTheme.BORDER_SUBTLE
                )
    
    def _close_terminal(self, terminal_name: str):
        """Close a terminal session"""
        if terminal_name not in self.terminals:
            return
        
        # Confirm closure
        if len(self.terminals) > 1:
            if not messagebox.askyesno("Close Terminal", f"Close {terminal_name}?"):
                return
        
        # Stop terminal
        terminal = self.terminals[terminal_name]
        terminal.stop_terminal()
        
        # Remove from managers
        self.terminal_manager.remove_terminal(terminal_name)
        
        # Remove widgets
        if terminal_name in self.terminal_widgets:
            self.terminal_widgets[terminal_name].destroy()
            del self.terminal_widgets[terminal_name]
        
        if terminal_name in self.tab_buttons:
            self.tab_buttons[terminal_name].destroy()
            del self.tab_buttons[terminal_name]
        
        if terminal_name in self.input_buffers:
            del self.input_buffers[terminal_name]

        del self.terminals[terminal_name]
        if terminal_name in self.terminal_states:
            del self.terminal_states[terminal_name]
        
        # Switch to another terminal if available
        if self.terminals:
            next_terminal = list(self.terminals.keys())[0]
            self._show_terminal(next_terminal)
        else:
            self.current_terminal = None
    
    def _new_terminal(self):
        """Create new terminal session"""
        terminal_name = self.terminal_manager.create_terminal(self.ssh_manager.client)
        self.add_terminal(terminal_name)
    
    def _on_key_press(self, terminal_name: str, event):
        """Handle key press in terminal"""
        if terminal_name not in self.terminals:
            return
        
        terminal = self.terminals[terminal_name]
        char = event.char
        
        # Handle special keys
        if event.keysym == "Return":
            char = "\n"
            buffer = self.input_buffers.get(terminal_name, "").strip()
            if buffer.startswith("sedit "):
                try:
                    _, filename = buffer.split(" ", 1)
                    self._open_text_editor(filename)
                except ValueError:
                    # Handle case where there's no filename
                    pass 
                self.input_buffers[terminal_name] = ""
                terminal.send_input("\n") # Send newline for new prompt
                return

            self.input_buffers[terminal_name] = ""
        elif event.keysym == "BackSpace":
            char = "\b"
            if terminal_name in self.input_buffers:
                self.input_buffers[terminal_name] = self.input_buffers[terminal_name][:-1]
        elif len(char) == 1 and char.isprintable():
            self.input_buffers.setdefault(terminal_name, "")
            self.input_buffers[terminal_name] += char
        
        if char:
            terminal.send_input(char)

    def _open_text_editor(self, filename: str):
        """Open the text editor for a remote file."""
        editor = TextEditorWindow(self.parent, self.ssh_manager, filename)
        editor.grab_set()
    
    def _on_terminal_output(self, terminal_name: str, data: str):
        """Handle terminal output"""
        if terminal_name not in self.terminal_widgets:
            return
        
        processed_data = self._process_terminal_output(data)
        
        # Update text widget in main thread
        def update_text():
            text_widget = self.terminal_widgets[terminal_name].text_widget
            text_widget.configure(state="normal")
            self._parse_and_insert_ansi(terminal_name, processed_data)
            text_widget.configure(state="disabled")
            text_widget.see("end")
        
        # Schedule update in main thread
        self.parent.after(0, update_text)

    def _parse_and_insert_ansi(self, terminal_name, data):
        """Parse ANSI escape codes and insert text with tags"""
        text_widget = self.terminal_widgets[terminal_name].text_widget
        current_tags = self.terminal_states[terminal_name]['tags']
        
        ansi_escape_pattern = re.compile(r'\x1b\[([0-9;?]*)([a-zA-Z])')
        parts = ansi_escape_pattern.split(data)

        text_to_insert = parts.pop(0)
        if text_to_insert:
            text_widget.insert("insert", text_to_insert, tuple(current_tags))

        for i in range(0, len(parts), 3):
            params_str = parts[i]
            command = parts[i+1]
            text_part = parts[i+2]

            params = [int(p) if p else 0 for p in params_str.split(';')]

            if command == 'm': # Graphics mode
                self._handle_sgr_codes(current_tags, params)
            elif command == 'H' or command == 'f': # Cursor position
                line = params[0] if len(params) > 0 else 1
                col = params[1] if len(params) > 1 else 1
                text_widget.mark_set("insert", f"{line}.{col-1}")
            elif command == 'J': # Erase in display
                if params[0] == 2: # Clear entire screen
                    text_widget.delete("1.0", "end")
            elif command == 'K': # Erase in line
                if params[0] == 0: # Erase from cursor to end of line
                    text_widget.delete("insert", "insert lineend")
                elif params[0] == 1: # Erase from start of line to cursor
                    text_widget.delete("insert linestart", "insert")
                elif params[0] == 2: # Erase entire line
                    text_widget.delete("insert linestart", "insert lineend")
            elif command == 'G': # Cursor horizontal absolute
                col = params[0] if params else 1
                line_info = text_widget.index("insert").split('.')[0]
                text_widget.mark_set("insert", f"{line_info}.{col-1}")


            if text_part:
                text_widget.insert("insert", text_part, tuple(current_tags))

    def _handle_sgr_codes(self, current_tags, codes):
        """Handles Select Graphic Rendition (SGR) codes."""
        if not codes or codes[0] == 0:  # Reset
            current_tags.clear()
            return

        i = 0
        while i < len(codes):
            code = codes[i]
            if code == 0:  # Reset
                current_tags.clear()
            elif code in self.fg_colors:
                current_tags.difference_update({self.ansi_color_map[c] for c in self.fg_colors})
                current_tags.add(self.ansi_color_map[code])
            elif code in self.bg_colors:
                current_tags.difference_update({self.ansi_color_map[c] for c in self.bg_colors})
                current_tags.add(self.ansi_color_map[code])
            elif code == 39: # default fg
                current_tags.difference_update({self.ansi_color_map[c] for c in self.fg_colors})
            elif code == 49: # default bg
                current_tags.difference_update({self.ansi_color_map[c] for c in self.bg_colors})
            elif tag := self.ansi_color_map.get(code):
                if tag == 'normal':
                    current_tags.discard('bold')
                    current_tags.discard('dim')
                elif tag == 'no_underline':
                    current_tags.discard('underline')
                else:
                    current_tags.add(tag)
            i += 1
    
    def _process_terminal_output(self, text: str) -> str:
        """Process terminal output with minimal ANSI cleaning"""
        import re
        
        # Only remove the most problematic sequences that cause display issues
        # Remove bracketed paste mode sequences
        text = re.sub(r'\x1b\[\?2004[hl]', '', text)
        
        # Remove title sequences
        text = re.sub(r'\x1b\]0;[^\x07]*\x07', '', text)
        
        # Remove some problematic mode sequences but keep essential ones
        text = re.sub(r'\x1b\[\?1049[hl]', '', text)  # Alternative screen buffer
        text = re.sub(r'\x1b\[\?1[hl]', '', text)     # Application cursor keys
        text = re.sub(r'\x1b\[\?25[hl]', '', text)    # Cursor visibility
        
        # Keep most other ANSI sequences as they are needed for proper terminal function
        
        return text
    
    
    
    def get_current_terminal(self) -> Optional[SSHTerminal]:
        """Get current active terminal"""
        if self.current_terminal and self.current_terminal in self.terminals:
            return self.terminals[self.current_terminal]
        return None
    
    def get_terminal_count(self) -> int:
        """Get number of active terminals"""
        return len(self.terminals)
    
    def send_command_to_current(self, command: str):
        """Send command to current terminal"""
        terminal = self.get_current_terminal()
        if terminal:
            terminal.send_command(command)
    
    def close_all_terminals(self):
        """Close all terminal sessions"""
        for terminal_name in list(self.terminals.keys()):
            self._close_terminal(terminal_name)
