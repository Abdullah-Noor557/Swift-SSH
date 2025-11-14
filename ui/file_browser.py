"""
Remote file browser with navigation and file operations
Handles file listing, navigation, and basic file operations
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import threading
from typing import Optional, Callable, List, Dict, Any
from core.ssh_manager import SSHManager
from core.scp_manager import SCPManager
from ui.theme import ModernTheme, get_file_icon_color, get_button_style, get_modern_font

class FileBrowser:
    def __init__(self, parent, ssh_manager: SSHManager, scp_manager: SCPManager, 
                 operation_callback: Optional[Callable] = None):
        self.parent = parent
        self.ssh_manager = ssh_manager
        self.scp_manager = scp_manager
        self.operation_callback = operation_callback
        self.current_path = "/home"
        self.file_list = []
        
        # Performance optimization: pagination for large directories
        self.items_per_page = 100
        self.current_page = 0
        self.total_pages = 0
        self.filtered_file_list = []
        
        # Create UI
        self._create_ui()
        
        # Load initial directory
        self._refresh_file_list()
        
        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        # Add tooltips for better UX
        self._add_tooltips()
    
    def _add_tooltips(self):
        """Add tooltips to UI elements"""
        try:
            from ui.theme import create_tooltip
            create_tooltip(self.home_btn, "Go to home directory")
            create_tooltip(self.up_btn, "Go up one directory (Backspace)")
            create_tooltip(self.refresh_btn, "Refresh file list (F5)")
            create_tooltip(self.upload_btn, "Upload files to server (Ctrl+U)")
            create_tooltip(self.download_btn, "Download selected files (Ctrl+D)")
            create_tooltip(self.new_folder_btn, "Create new folder (Ctrl+N)")
            create_tooltip(self.delete_btn, "Delete selected files (Delete)")
            create_tooltip(self.path_entry, "Enter path and press Enter to navigate")
        except Exception:
            pass  # Tooltips are optional
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for better UX"""
        # F5 to refresh
        self.file_tree.bind("<F5>", lambda e: self._refresh_file_list())
        # Delete key to delete selected
        self.file_tree.bind("<Delete>", lambda e: self._delete_selected())
        # Ctrl+U to upload
        self.parent.bind("<Control-u>", lambda e: self._upload_files())
        # Ctrl+D to download
        self.parent.bind("<Control-d>", lambda e: self._download_selected())
        # Backspace to go up
        self.file_tree.bind("<BackSpace>", lambda e: self._go_up())
        # Ctrl+N for new folder
        self.parent.bind("<Control-n>", lambda e: self._create_folder())
    
    def _create_ui(self):
        """Create the file browser UI"""
        # Configure parent grid to fill available space
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(0, weight=1)
        
        # Create main frame for proper layout
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # Configure grid for main frame
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)  # File list gets all the space
        main_frame.grid_rowconfigure(0, weight=0)  # Navigation bar fixed height
        main_frame.grid_rowconfigure(2, weight=0)  # Toolbar fixed height
        
        # Store main frame reference
        self.main_frame = main_frame
        
        # Navigation bar
        self._create_navigation_bar()
        
        # File list area
        self._create_file_list_area()
        
        # Toolbar
        self._create_toolbar()
    
    def _create_navigation_bar(self):
        """Create modern navigation bar with breadcrumbs"""
        nav_frame = ctk.CTkFrame(self.main_frame, fg_color=ModernTheme.BG_CARD, height=58, corner_radius=0)
        nav_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        nav_frame.grid_propagate(False)
        
        # Left navigation buttons
        nav_buttons = ctk.CTkFrame(nav_frame, fg_color="transparent")
        nav_buttons.pack(side="left", padx=16, pady=10)
        
        primary_style = get_button_style("primary")
        outline_style = get_button_style("outline")
        secondary_style = get_button_style("secondary")
        
        # Home button with enhanced icon
        self.home_btn = ctk.CTkButton(
            nav_buttons,
            text="🏠",
            command=self._go_home,
            width=44,
            height=38,
            font=("Segoe UI Emoji", 15),
            **primary_style
        )
        self.home_btn.pack(side="left", padx=(0, 8))
        
        # Up button with enhanced icon
        self.up_btn = ctk.CTkButton(
            nav_buttons,
            text="⬆",
            command=self._go_up,
            width=44,
            height=38,
            font=("Segoe UI Emoji", 15),
            **secondary_style
        )
        self.up_btn.pack(side="left", padx=(0, 8))
        
        # Refresh button with enhanced icon
        self.refresh_btn = ctk.CTkButton(
            nav_buttons,
            text="🔄",
            command=self._refresh_file_list,
            width=44,
            height=38,
            font=("Segoe UI Emoji", 15),
            **outline_style
        )
        self.refresh_btn.pack(side="left")
        
        # Path entry with enhanced modern styling
        path_container = ctk.CTkFrame(nav_frame, fg_color="transparent")
        path_container.pack(side="left", fill="x", expand=True, padx=(10, 16), pady=10)
        
        self.path_var = ctk.StringVar(value=self.current_path)
        self.path_entry = ctk.CTkEntry(
            path_container,
            textvariable=self.path_var,
            placeholder_text="📁 /path/to/directory",
            fg_color=ModernTheme.BG_INPUT,
            border_color=ModernTheme.BORDER_PRIMARY,
            border_width=2,
            corner_radius=8,
            font=get_modern_font(11),
            height=38
        )
        self.path_entry.pack(fill="x", expand=True)
        self.path_entry.bind("<Return>", lambda e: self._navigate_to_path())
    
    def _create_file_list_area(self):
        """Create modern file list area with scrollbar"""
        # File list frame with enhanced card styling
        list_frame = ctk.CTkFrame(self.main_frame, fg_color=ModernTheme.BG_CARD, corner_radius=0)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        
        # Create Treeview for file list
        self._create_file_treeview(list_frame)
    
    def _create_file_treeview(self, parent):
        """Create Treeview for file listing with enhanced styling"""
        # Treeview frame with padding
        tree_frame = ctk.CTkFrame(parent, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=16, pady=16)
        
        # Create Treeview
        import tkinter as tk
        from tkinter import ttk
        
        # Configure modern style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Treeview styling with modern colors
        style.configure("Treeview", 
                       background=ModernTheme.BG_TERTIARY,
                       foreground=ModernTheme.TEXT_PRIMARY,
                       fieldbackground=ModernTheme.BG_TERTIARY,
                       borderwidth=0,
                       rowheight=32,
                       font=get_modern_font(10))
        
        style.configure("Treeview.Heading",
                       background=ModernTheme.BG_SECONDARY,
                       foreground=ModernTheme.TEXT_SECONDARY,
                       borderwidth=1,
                       relief="flat",
                       font=get_modern_font(10, "semibold"))
        
        # Row selection colors
        style.map("Treeview",
                 background=[("selected", ModernTheme.ACCENT_PRIMARY)],
                 foreground=[("selected", ModernTheme.TEXT_PRIMARY)])
        
        # Create Treeview with enhanced columns
        self.file_tree = ttk.Treeview(tree_frame, columns=("size", "permissions", "modified"), show="tree headings")
        self.file_tree.heading("#0", text="📄 Name", anchor="w")
        self.file_tree.heading("size", text="💾 Size", anchor="w")
        self.file_tree.heading("permissions", text="🔒 Permissions", anchor="w")
        self.file_tree.heading("modified", text="🕐 Modified", anchor="w")
        
        # Configure columns with better sizing
        self.file_tree.column("#0", width=350, minwidth=250)
        self.file_tree.column("size", width=120, minwidth=100)
        self.file_tree.column("permissions", width=120, minwidth=100)
        self.file_tree.column("modified", width=160, minwidth=140)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.file_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack components
        self.file_tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Bind events
        self.file_tree.bind("<Double-1>", self._on_double_click)
        self.file_tree.bind("<Button-3>", self._on_right_click)
        self.file_tree.bind("<Return>", self._on_enter_key)
    
    def _create_toolbar(self):
        """Create modern toolbar with file operations"""
        toolbar = ctk.CTkFrame(self.main_frame, fg_color=ModernTheme.BG_CARD, height=60, corner_radius=0)
        toolbar.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        toolbar.grid_propagate(False)
        
        # Left buttons group with enhanced styling
        left_buttons = ctk.CTkFrame(toolbar, fg_color="transparent")
        left_buttons.pack(side="left", padx=16, pady=10)
        
        primary_style = get_button_style("primary")
        secondary_style = get_button_style("secondary")
        success_style = get_button_style("success")
        danger_style = get_button_style("danger")
        
        # Upload button with enhanced styling
        self.upload_btn = ctk.CTkButton(
            left_buttons,
            text="📤 Upload",
            command=self._upload_files,
            width=120,
            height=40,
            font=get_modern_font(11, "semibold"),
            **primary_style
        )
        self.upload_btn.pack(side="left", padx=(0, 10))
        
        # Download button with enhanced styling
        self.download_btn = ctk.CTkButton(
            left_buttons,
            text="📥 Download",
            command=self._download_selected,
            width=130,
            height=40,
            font=get_modern_font(11, "semibold"),
            **success_style
        )
        self.download_btn.pack(side="left", padx=(0, 10))
        
        # New folder button with enhanced styling
        self.new_folder_btn = ctk.CTkButton(
            left_buttons,
            text="➕ New Folder",
            command=self._create_folder,
            width=140,
            height=40,
            font=get_modern_font(11, "semibold"),
            **secondary_style
        )
        self.new_folder_btn.pack(side="left")
        
        # Middle section - Pagination controls
        middle_buttons = ctk.CTkFrame(toolbar, fg_color="transparent")
        middle_buttons.pack(side="left", expand=True, padx=16, pady=10)
        
        outline_style = get_button_style("outline")
        
        # Pagination label
        self.page_label = ctk.CTkLabel(
            middle_buttons,
            text="Page 1 of 1",
            font=get_modern_font(10),
            text_color=ModernTheme.TEXT_SECONDARY
        )
        self.page_label.pack(side="left", padx=10)
        
        # Previous page button
        self.prev_page_btn = ctk.CTkButton(
            middle_buttons,
            text="◀",
            command=self._prev_page,
            width=40,
            height=32,
            font=get_modern_font(14),
            state="disabled",
            **outline_style
        )
        self.prev_page_btn.pack(side="left", padx=2)
        
        # Next page button
        self.next_page_btn = ctk.CTkButton(
            middle_buttons,
            text="▶",
            command=self._next_page,
            width=40,
            height=32,
            font=get_modern_font(14),
            state="disabled",
            **outline_style
        )
        self.next_page_btn.pack(side="left", padx=2)
        
        # Right buttons group with enhanced styling
        right_buttons = ctk.CTkFrame(toolbar, fg_color="transparent")
        right_buttons.pack(side="right", padx=16, pady=10)
        
        # Delete button with enhanced styling
        self.delete_btn = ctk.CTkButton(
            right_buttons,
            text="🗑 Delete",
            command=self._delete_selected,
            width=110,
            height=40,
            font=get_modern_font(11, "semibold"),
            **danger_style
        )
        self.delete_btn.pack(side="left")
    
    def _refresh_file_list(self):
        """Refresh the file list"""
        def load_files():
            try:
                files = self.ssh_manager.get_file_list(self.current_path)
                self.parent.after(0, lambda: self._update_file_list(files))
            except Exception as e:
                self.parent.after(0, lambda: self._show_error(f"Error loading files: {e}"))
        
        # Show loading state
        self._clear_file_list()
        self._add_loading_item()
        
        # Load files in background
        threading.Thread(target=load_files, daemon=True).start()
    
    def _update_file_list(self, files: List[Dict]):
        """Update the file list display with pagination"""
        self.file_list = files
        self.filtered_file_list = files
        self.current_page = 0
        
        # Calculate total pages
        self.total_pages = max(1, (len(self.filtered_file_list) + self.items_per_page - 1) // self.items_per_page)
        
        # Display first page
        self._display_current_page()
        
        # Update pagination controls
        self._update_pagination_controls()
    
    def _display_current_page(self):
        """Display files for current page"""
        self._clear_file_list()
        
        # Add parent directory entry
        if self.current_path != "/":
            self.file_tree.insert("", "end", text="..", values=("", "", ""), tags=("parent",))
        
        # Calculate page range
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.filtered_file_list))
        
        # Add files and directories for current page
        for file_info in self.filtered_file_list[start_idx:end_idx]:
            name = file_info["name"]
            size = self._format_size(file_info["size"])
            permissions = file_info["permissions"]
            modified = self._format_date(file_info["modified"])
            
            # Determine icon and tags
            if file_info["is_directory"]:
                icon = "📁"
                tags = ("directory",)
            else:
                icon = self._get_file_icon(name)
                tags = ("file",)
            
            # Insert item
            self.file_tree.insert("", "end", text=f"{icon} {name}", 
                                values=(size, permissions, modified), tags=tags)
        
        # Configure tags with modern colors
        self.file_tree.tag_configure("directory", foreground=ModernTheme.ACCENT_WARNING)
        self.file_tree.tag_configure("file", foreground=ModernTheme.TEXT_PRIMARY)
        self.file_tree.tag_configure("parent", foreground=ModernTheme.TEXT_MUTED)
    
    def _update_pagination_controls(self):
        """Update pagination button states and label"""
        # Update label
        total_items = len(self.filtered_file_list)
        self.page_label.configure(
            text=f"Page {self.current_page + 1} of {self.total_pages} ({total_items} items)"
        )
        
        # Update button states
        if self.current_page > 0:
            self.prev_page_btn.configure(state="normal")
        else:
            self.prev_page_btn.configure(state="disabled")
        
        if self.current_page < self.total_pages - 1:
            self.next_page_btn.configure(state="normal")
        else:
            self.next_page_btn.configure(state="disabled")
    
    def _prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self._display_current_page()
            self._update_pagination_controls()
    
    def _next_page(self):
        """Go to next page"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._display_current_page()
            self._update_pagination_controls()
    
    def _clear_file_list(self):
        """Clear the file list"""
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
    
    def _add_loading_item(self):
        """Add loading indicator"""
        self.file_tree.insert("", "end", text="Loading...", values=("", "", ""))
    
    def _format_size(self, size: int) -> str:
        """Format file size"""
        if size == 0:
            return "-"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def _format_date(self, timestamp: float) -> str:
        """Format modification date"""
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")
    
    def _get_file_icon(self, filename: str) -> str:
        """Get modern icon for file type"""
        ext = os.path.splitext(filename)[1].lower()
        icon_map = {
            # Text files
            '.txt': '📄', '.md': '📝', '.doc': '📘', '.docx': '📘', '.pdf': '📕',
            # Code files
            '.py': '🐍', '.js': '📜', '.ts': '💙', '.java': '☕', '.cpp': '⚙',
            '.c': '⚙', '.h': '📋', '.go': '🔷', '.rs': '🦀', '.php': '🐘',
            '.rb': '💎', '.swift': '🦅', '.kt': '🔶',
            # Web files
            '.html': '🌐', '.css': '🎨', '.scss': '🎨', '.json': '📋', '.xml': '📋',
            # Images
            '.jpg': '🖼', '.jpeg': '🖼', '.png': '🖼', '.gif': '🖼', '.svg': '🎨',
            '.bmp': '🖼', '.ico': '🖼',
            # Archives
            '.zip': '📦', '.rar': '📦', '.tar': '📦', '.gz': '📦', '.7z': '📦',
            # Executables
            '.exe': '⚙', '.sh': '🔧', '.bat': '🔧', '.cmd': '🔧',
            # Logs and configs
            '.log': '📋', '.conf': '⚙', '.config': '⚙', '.ini': '⚙', '.yaml': '⚙', '.yml': '⚙',
            # Data
            '.db': '🗄', '.sql': '🗄', '.sqlite': '🗄', '.csv': '📊'
        }
        return icon_map.get(ext, '📄')
    
    def _on_double_click(self, event):
        """Handle double-click on file/directory"""
        selection = self.file_tree.selection()
        if not selection:
            return
        
        item = self.file_tree.item(selection[0])
        text = item["text"]
        
        # Handle parent directory
        if text == "..":
            self._go_up()
            return
        
        # Remove icon from text
        name = text.split(" ", 1)[1] if " " in text else text
        
        # Check if it's a directory
        for file_info in self.file_list:
            if file_info["name"] == name and file_info["is_directory"]:
                self._navigate_to_directory(name)
                return
        
        # For files, we could open them or show properties
        self._show_file_properties(name)
    
    def _on_right_click(self, event):
        """Handle right-click context menu"""
        selection = self.file_tree.selection()
        if not selection:
            return
        
        # Create context menu
        context_menu = ctk.CTkToplevel(self.parent)
        context_menu.title("File Operations")
        context_menu.geometry("200x150")
        context_menu.attributes("-topmost", True)
        
        # Add context menu options
        ctk.CTkButton(context_menu, text="Download", command=self._download_selected).pack(pady=5)
        ctk.CTkButton(context_menu, text="Delete", command=self._delete_selected).pack(pady=5)
        ctk.CTkButton(context_menu, text="Properties", command=self._show_properties).pack(pady=5)
    
    def _on_enter_key(self, event):
        """Handle Enter key press"""
        self._on_double_click(event)
    
    def _navigate_to_directory(self, dir_name: str):
        """Navigate to a directory"""
        if self.current_path == "/":
            new_path = f"/{dir_name}"
        else:
            new_path = f"{self.current_path}/{dir_name}"
        
        self.current_path = new_path
        self.path_var.set(self.current_path)
        self._refresh_file_list()
    
    def _navigate_to_path(self):
        """Navigate to path entered in path bar"""
        new_path = self.path_var.get().strip()
        if new_path:
            self.current_path = new_path
            self._refresh_file_list()
    
    def _go_home(self):
        """Go to home directory"""
        self.current_path = "/home"
        self.path_var.set(self.current_path)
        self._refresh_file_list()
    
    def _go_up(self):
        """Go up one directory level"""
        if self.current_path != "/":
            self.current_path = os.path.dirname(self.current_path)
            if not self.current_path:
                self.current_path = "/"
            self.path_var.set(self.current_path)
            self._refresh_file_list()
    
    def _upload_files(self):
        """Upload files to current directory"""
        files = filedialog.askopenfilenames(title="Select files to upload")
        if not files:
            return
        
        def upload_thread():
            for file_path in files:
                filename = os.path.basename(file_path)
                remote_path = f"{self.current_path}/{filename}"
                
                def progress_callback(transfer_id, progress, speed, transferred, total):
                    if self.operation_callback:
                        self.operation_callback("Upload", f"{filename}: {progress:.1f}%")
                
                success = self.scp_manager.upload_file(file_path, remote_path, progress_callback)
                if not success:
                    self.parent.after(0, lambda: self._show_error(f"Failed to upload {filename}"))
                    return
            
            self.parent.after(0, self._refresh_file_list)
            if self.operation_callback:
                self.operation_callback("Upload", "Upload completed")
        
        threading.Thread(target=upload_thread, daemon=True).start()
    
    def _download_selected(self):
        """Download selected files"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select files to download")
            return
        
        # Get download directory
        download_dir = filedialog.askdirectory(title="Select download directory")
        if not download_dir:
            return
        
        def download_thread():
            for item in selection:
                file_item = self.file_tree.item(item)
                text = file_item["text"]
                name = text.split(" ", 1)[1] if " " in text else text
                
                if name == "..":
                    continue
                
                remote_path = f"{self.current_path}/{name}"
                local_path = os.path.join(download_dir, name)
                
                def progress_callback(transfer_id, progress, speed, transferred, total):
                    if self.operation_callback:
                        self.operation_callback("Download", f"{name}: {progress:.1f}%")
                
                success = self.scp_manager.download_file(remote_path, local_path, progress_callback)
                if not success:
                    self.parent.after(0, lambda: self._show_error(f"Failed to download {name}"))
                    return
            
            self.parent.after(0, lambda: self._show_success("Download completed"))
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def _create_folder(self):
        """Create new folder"""
        folder_name = ctk.CTkInputDialog(text="Enter folder name:", title="New Folder").get_input()
        if not folder_name:
            return
        
        remote_path = f"{self.current_path}/{folder_name}"
        success = self.ssh_manager.create_directory(remote_path)
        
        if success:
            self._refresh_file_list()
            if self.operation_callback:
                self.operation_callback("Create", f"Created folder: {folder_name}")
        else:
            self._show_error(f"Failed to create folder: {folder_name}")
    
    def _delete_selected(self):
        """Delete selected files"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select files to delete")
            return
        
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete selected items?"):
            return
        
        def delete_thread():
            for item in selection:
                file_item = self.file_tree.item(item)
                text = file_item["text"]
                name = text.split(" ", 1)[1] if " " in text else text
                
                if name == "..":
                    continue
                
                remote_path = f"{self.current_path}/{name}"
                
                # Check if it's a directory
                is_directory = False
                for file_info in self.file_list:
                    if file_info["name"] == name and file_info["is_directory"]:
                        is_directory = True
                        break
                
                if is_directory:
                    success = self.ssh_manager.delete_directory(remote_path)
                else:
                    success = self.ssh_manager.delete_file(remote_path)
                
                if not success:
                    self.parent.after(0, lambda: self._show_error(f"Failed to delete {name}"))
                    return
            
            self.parent.after(0, self._refresh_file_list)
            if self.operation_callback:
                self.operation_callback("Delete", "Deletion completed")
        
        threading.Thread(target=delete_thread, daemon=True).start()
    
    def _show_file_properties(self, filename: str):
        """Show file properties"""
        remote_path = f"{self.current_path}/{filename}"
        file_info = self.ssh_manager.get_file_info(remote_path)
        
        if file_info:
            properties = f"""File Properties:
Name: {file_info['name']}
Size: {self._format_size(file_info['size'])}
Permissions: {file_info['permissions']}
Modified: {self._format_date(file_info['modified'])}
Path: {remote_path}"""
            
            messagebox.showinfo("File Properties", properties)
    
    def _show_properties(self):
        """Show properties of selected file"""
        selection = self.file_tree.selection()
        if not selection:
            return
        
        file_item = self.file_tree.item(selection[0])
        text = file_item["text"]
        name = text.split(" ", 1)[1] if " " in text else text
        
        if name != "..":
            self._show_file_properties(name)
    
    def _show_error(self, message: str):
        """Show error message"""
        messagebox.showerror("Error", message)
    
    def _show_success(self, message: str):
        """Show success message"""
        messagebox.showinfo("Success", message)
