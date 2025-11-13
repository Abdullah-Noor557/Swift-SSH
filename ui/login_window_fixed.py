"""
Fixed login window with working password field
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
from typing import Optional, Callable
import threading
import ipaddress
from core.network_discovery import detect_local_networks, discover_all_local, scan_network, listen_for_beacons
from core.profile_manager import ProfileManager
from core.ssh_manager import SSHManager
from ui.theme import ModernTheme, apply_theme, get_button_style, get_card_style, get_input_style, create_tooltip, get_modern_font

class LoginWindow:
    def __init__(self, on_connect_callback: Optional[Callable] = None):
        self.on_connect_callback = on_connect_callback
        self.profile_manager = ProfileManager()
        self.ssh_manager = SSHManager()
        
        # Create main window
        self.window = ctk.CTk()
        self.window.title("SwiftSSH - Connect to Server")
        self.window.geometry("550x720")
        self.window.resizable(False, True)
        
        # Set minimum size
        self.window.minsize(500, 650)
        
        # Apply theme
        apply_theme()
        
        # Center window
        self._center_window()
        
        # Create UI
        self._create_ui()
        
        # Load saved profiles
        self._load_profiles()
    
    def _center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_ui(self):
        """Create the login UI"""
        # Main scrollable frame (allows scrolling on smaller windows)
        main_frame = ctk.CTkScrollableFrame(
            self.window, 
            fg_color=ModernTheme.BG_PRIMARY,
            scrollbar_button_color=ModernTheme.SCROLLBAR_FG
        )
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Header section with modern design
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(pady=(30, 30), fill="x", padx=40)
        
        # App icon with gradient-like styling
        logo_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        logo_container.pack(pady=(0, 15))
        
        logo_label = ctk.CTkLabel(
            logo_container,
            text="⚡",
            font=("Segoe UI Emoji", 56),
            text_color=ModernTheme.ACCENT_PRIMARY
        )
        logo_label.pack()
        
        # Title with enhanced typography
        title_label = ctk.CTkLabel(
            header_frame,
            text="SwiftSSH",
            font=get_modern_font(36, "bold"),
            text_color=ModernTheme.TEXT_PRIMARY
        )
        title_label.pack(pady=(0, 8))
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Secure & Fast SSH Client",
            font=get_modern_font(12),
            text_color=ModernTheme.TEXT_TERTIARY
        )
        subtitle_label.pack(pady=(0, 5))
        
        # Version badge
        version_badge = ctk.CTkFrame(header_frame, fg_color=ModernTheme.BG_TERTIARY, corner_radius=16)
        version_badge.pack(pady=(8, 0))
        
        version_label = ctk.CTkLabel(
            version_badge,
            text="v1.0",
            font=get_modern_font(9, "semibold"),
            text_color=ModernTheme.TEXT_MUTED
        )
        version_label.pack(padx=12, pady=4)
        
        # Profile selection card with enhanced styling
        card_style = get_card_style()
        profile_frame = ctk.CTkFrame(main_frame, **card_style)
        profile_frame.pack(fill="x", padx=40, pady=(0, 18))
        
        # Card header with icon and description
        card_header = ctk.CTkFrame(profile_frame, fg_color="transparent")
        card_header.pack(fill="x", padx=24, pady=(24, 8))
        
        header_left = ctk.CTkFrame(card_header, fg_color="transparent")
        header_left.pack(side="left", fill="x", expand=True)
        
        title_row = ctk.CTkFrame(header_left, fg_color="transparent")
        title_row.pack(anchor="w")
        
        ctk.CTkLabel(
            title_row,
            text="💾",
            font=("Segoe UI Emoji", 16),
            text_color=ModernTheme.ACCENT_INFO
        ).pack(side="left", padx=(0, 8))
        
        ctk.CTkLabel(
            title_row,
            text="Saved Connections",
            font=get_modern_font(14, "bold"),
            text_color=ModernTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(side="left")
        
        ctk.CTkLabel(
            header_left,
            text="Select a saved profile or create a new connection",
            font=get_modern_font(10),
            text_color=ModernTheme.TEXT_MUTED,
            anchor="w"
        ).pack(anchor="w", pady=(4, 0))
        
        # Profile dropdown with enhanced styling
        dropdown_container = ctk.CTkFrame(profile_frame, fg_color="transparent")
        dropdown_container.pack(fill="x", padx=24, pady=(12, 0))
        
        self.profile_var = ctk.StringVar(value="New Connection")
        input_style = get_input_style()
        self.profile_dropdown = ctk.CTkComboBox(
            dropdown_container,
            variable=self.profile_var,
            values=["New Connection"],
            command=self._on_profile_selected,
            **input_style,
            button_color=ModernTheme.ACCENT_PRIMARY,
            button_hover_color=ModernTheme.ACCENT_HIGHLIGHT,
            dropdown_fg_color=ModernTheme.BG_TERTIARY,
            font=get_modern_font(11),
            height=44
        )
        self.profile_dropdown.pack(fill="x")
        
        # Profile management buttons with enhanced styling
        profile_buttons_frame = ctk.CTkFrame(profile_frame, fg_color="transparent")
        profile_buttons_frame.pack(fill="x", padx=24, pady=(16, 24))
        
        outline_style = get_button_style("outline")
        secondary_style = get_button_style("secondary")
        danger_style = get_button_style("danger")
        
        self.load_button = ctk.CTkButton(
            profile_buttons_frame,
            text="📂 Load",
            command=self._load_selected_profile,
            width=110,
            height=38,
            font=get_modern_font(11, "semibold"),
            **outline_style
        )
        self.load_button.pack(side="left", padx=(0, 8))
        
        self.save_button = ctk.CTkButton(
            profile_buttons_frame,
            text="💾 Save",
            command=self._save_current_profile,
            width=110,
            height=38,
            font=get_modern_font(11, "semibold"),
            **secondary_style
        )
        self.save_button.pack(side="left", padx=(0, 8))
        
        self.delete_button = ctk.CTkButton(
            profile_buttons_frame,
            text="🗑 Delete",
            command=self._delete_selected_profile,
            width=110,
            height=38,
            font=get_modern_font(11, "semibold"),
            **danger_style
        )
        self.delete_button.pack(side="left")
        
        # Network Discovery card
        self._build_discovery_card(main_frame, card_style)

        # Connection form card with enhanced styling
        form_frame = ctk.CTkFrame(main_frame, **card_style)
        form_frame.pack(fill="x", padx=40, pady=(0, 20))
        
        # Form header with icon and description
        form_header = ctk.CTkFrame(form_frame, fg_color="transparent")
        form_header.pack(fill="x", padx=24, pady=(24, 20))
        
        header_left = ctk.CTkFrame(form_header, fg_color="transparent")
        header_left.pack(side="left", fill="x", expand=True)
        
        title_row = ctk.CTkFrame(header_left, fg_color="transparent")
        title_row.pack(anchor="w")
        
        ctk.CTkLabel(
            title_row,
            text="🔐",
            font=("Segoe UI Emoji", 16),
            text_color=ModernTheme.ACCENT_SUCCESS
        ).pack(side="left", padx=(0, 8))
        
        ctk.CTkLabel(
            title_row,
            text="Connection Details",
            font=get_modern_font(14, "bold"),
            text_color=ModernTheme.TEXT_PRIMARY,
            anchor="w"
        ).pack(side="left")
        
        ctk.CTkLabel(
            header_left,
            text="Enter your server credentials to establish a secure connection",
            font=get_modern_font(10),
            text_color=ModernTheme.TEXT_MUTED,
            anchor="w"
        ).pack(anchor="w", pady=(4, 0))
        
        # Host field with enhanced styling
        host_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        host_frame.pack(fill="x", padx=24, pady=(0, 16))
        
        host_label_row = ctk.CTkFrame(host_frame, fg_color="transparent")
        host_label_row.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(
            host_label_row,
            text="🌐",
            font=("Segoe UI Emoji", 12),
            text_color=ModernTheme.ACCENT_PRIMARY
        ).pack(side="left", padx=(0, 6))
        
        ctk.CTkLabel(
            host_label_row,
            text="Host Address",
            font=get_modern_font(11, "semibold"),
            text_color=ModernTheme.TEXT_SECONDARY,
            anchor="w"
        ).pack(side="left")
        
        self.host_entry = ctk.CTkEntry(
            host_frame,
            placeholder_text="192.168.1.100 or example.com",
            **input_style,
            font=get_modern_font(11),
            height=46
        )
        self.host_entry.pack(fill="x")
        
        # Username field with enhanced styling
        username_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        username_frame.pack(fill="x", padx=24, pady=(0, 16))
        
        username_label_row = ctk.CTkFrame(username_frame, fg_color="transparent")
        username_label_row.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(
            username_label_row,
            text="👤",
            font=("Segoe UI Emoji", 12),
            text_color=ModernTheme.ACCENT_SECONDARY
        ).pack(side="left", padx=(0, 6))
        
        ctk.CTkLabel(
            username_label_row,
            text="Username",
            font=get_modern_font(11, "semibold"),
            text_color=ModernTheme.TEXT_SECONDARY,
            anchor="w"
        ).pack(side="left")
        
        self.username_entry = ctk.CTkEntry(
            username_frame,
            placeholder_text="root, admin, ubuntu...",
            **input_style,
            font=get_modern_font(11),
            height=46
        )
        self.username_entry.pack(fill="x")
        
        # Password field with enhanced styling
        password_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        password_frame.pack(fill="x", padx=24, pady=(0, 16))
        
        password_label_row = ctk.CTkFrame(password_frame, fg_color="transparent")
        password_label_row.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(
            password_label_row,
            text="🔑",
            font=("Segoe UI Emoji", 12),
            text_color=ModernTheme.ACCENT_WARNING
        ).pack(side="left", padx=(0, 6))
        
        ctk.CTkLabel(
            password_label_row,
            text="Password",
            font=get_modern_font(11, "semibold"),
            text_color=ModernTheme.TEXT_SECONDARY,
            anchor="w"
        ).pack(side="left")
        
        self.password_entry = ctk.CTkEntry(
            password_frame,
            placeholder_text="Enter your password",
            show="●",
            **input_style,
            font=get_modern_font(11),
            height=46
        )
        self.password_entry.pack(fill="x")
        # Allow pressing Enter to connect right away
        self.password_entry.bind("<Return>", lambda _e: self._connect())
        
        # Port field with enhanced styling
        port_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        port_frame.pack(fill="x", padx=24, pady=(0, 24))
        
        port_label_row = ctk.CTkFrame(port_frame, fg_color="transparent")
        port_label_row.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(
            port_label_row,
            text="🔌",
            font=("Segoe UI Emoji", 12),
            text_color=ModernTheme.ACCENT_INFO
        ).pack(side="left", padx=(0, 6))
        
        ctk.CTkLabel(
            port_label_row,
            text="Port",
            font=get_modern_font(11, "semibold"),
            text_color=ModernTheme.TEXT_SECONDARY,
            anchor="w"
        ).pack(side="left")
        
        self.port_entry = ctk.CTkEntry(
            port_frame,
            placeholder_text="22 (default)",
            **input_style,
            font=get_modern_font(11),
            height=46,
            width=160
        )
        self.port_entry.pack(anchor="w")
        
        # Connect button with enhanced styling
        connect_style = get_button_style("primary")
        self.connect_button = ctk.CTkButton(
            main_frame,
            text="⚡ Connect to Server",
            command=self._connect,
            height=54,
            font=get_modern_font(14, "bold"),
            **connect_style
        )
        self.connect_button.pack(fill="x", padx=40, pady=(0, 20))
        
        # Status indicator with icon
        status_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        status_frame.pack(pady=(0, 20))
        
        self.status_indicator = ctk.CTkLabel(
            status_frame,
            text="●",
            font=get_modern_font(12),
            text_color=ModernTheme.STATUS_IDLE
        )
        self.status_indicator.pack(side="left", padx=(0, 6))
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready to connect",
            font=get_modern_font(10),
            text_color=ModernTheme.TEXT_MUTED
        )
        self.status_label.pack(side="left")
        
        # Footer with features info
        footer_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer_frame.pack(pady=(5, 20))
        
        features = ["🔒 Secure", "⚡ Fast", "🎯 Reliable"]
        for i, feature in enumerate(features):
            feature_label = ctk.CTkLabel(
                footer_frame,
                text=feature,
                font=get_modern_font(9),
                text_color=ModernTheme.TEXT_MUTED
            )
            feature_label.pack(side="left", padx=8 if i < len(features) - 1 else 0)
        
        # Focus on host field for better UX
        self.host_entry.focus_set()
        
        # Add keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        # Add tooltips for better UX
        self._add_tooltips()
    
    def _build_discovery_card(self, main_frame, card_style):
        discover_frame = ctk.CTkFrame(main_frame, **card_style)
        discover_frame.pack(fill="x", padx=40, pady=(0, 18))
        
        header = ctk.CTkFrame(discover_frame, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 8))
        
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        
        title_row = ctk.CTkFrame(left, fg_color="transparent")
        title_row.pack(anchor="w")
        
        ctk.CTkLabel(
            title_row,
            text="🔎",
            font=("Segoe UI Emoji", 16),
            text_color=ModernTheme.ACCENT_PRIMARY,
        ).pack(side="left", padx=(0, 8))
        
        ctk.CTkLabel(
            title_row,
            text="Discover SSH on Local Network",
            font=get_modern_font(14, "bold"),
            text_color=ModernTheme.TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left")
        
        ctk.CTkLabel(
            left,
            text="Scan your subnet(s) for hosts with SSH open and fill Host automatically",
            font=get_modern_font(10),
            text_color=ModernTheme.TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))
        
        # Mode row
        mode_row = ctk.CTkFrame(discover_frame, fg_color="transparent")
        mode_row.pack(fill="x", padx=24, pady=(8, 0))
        ctk.CTkLabel(
            mode_row,
            text="Mode",
            font=get_modern_font(10, "semibold"),
            text_color=ModernTheme.TEXT_SECONDARY,
        ).pack(side="left")
        self.discover_mode_var = ctk.StringVar(value="broadcast")
        self.mode_broadcast = ctk.CTkRadioButton(
            mode_row, text="Broadcast", variable=self.discover_mode_var, value="broadcast"
        )
        self.mode_broadcast.pack(side="left", padx=(12, 4))
        self.mode_scan = ctk.CTkRadioButton(
            mode_row, text="Port Scan", variable=self.discover_mode_var, value="scan"
        )
        self.mode_scan.pack(side="left", padx=(4, 12))

        # Controls row
        controls = ctk.CTkFrame(discover_frame, fg_color="transparent")
        controls.pack(fill="x", padx=24, pady=(8, 8))
        
        self.discover_subnet_entry = ctk.CTkEntry(
            controls,
            placeholder_text="auto-detect or enter CIDR e.g. 192.168.1.0/24",
            fg_color=ModernTheme.BG_TERTIARY,
            border_color=ModernTheme.BG_TERTIARY,
            text_color=ModernTheme.TEXT_PRIMARY,
            font=get_modern_font(10),
            height=40,
            width=260,
        )
        self.discover_subnet_entry.pack(side="left")
        
        secondary = get_button_style("secondary")
        primary = get_button_style("primary")
        danger = get_button_style("danger")
        
        self.discover_detect_btn = ctk.CTkButton(
            controls,
            text="Detect",
            command=self._discover_prefill_networks,
            height=36,
            width=90,
            font=get_modern_font(10, "semibold"),
            **secondary,
        )
        self.discover_detect_btn.pack(side="left", padx=(8, 0))
        
        self.discover_start_btn = ctk.CTkButton(
            controls,
            text="Start Scan",
            command=self._start_discover,
            height=36,
            width=110,
            font=get_modern_font(10, "semibold"),
            **primary,
        )
        self.discover_start_btn.pack(side="left", padx=(8, 0))
        
        self.discover_stop_btn = ctk.CTkButton(
            controls,
            text="Stop",
            command=self._stop_discover,
            height=36,
            width=90,
            font=get_modern_font(10, "semibold"),
            state="disabled",
            **danger,
        )
        self.discover_stop_btn.pack(side="left", padx=(8, 0))
        
        # Progress
        progress_row = ctk.CTkFrame(discover_frame, fg_color="transparent")
        progress_row.pack(fill="x", padx=24, pady=(0, 8))
        self.discover_progress_label = ctk.CTkLabel(
            progress_row,
            text="Idle",
            font=get_modern_font(10),
            text_color=ModernTheme.TEXT_SECONDARY,
        )
        self.discover_progress_label.pack(anchor="w")
        self.discover_progress = ctk.CTkProgressBar(
            progress_row,
            height=8,
            progress_color=ModernTheme.ACCENT_PRIMARY,
        )
        self.discover_progress.set(0)
        self.discover_progress.pack(fill="x")
        
        # Results list
        results_container = ctk.CTkFrame(discover_frame, fg_color=ModernTheme.BG_TERTIARY, corner_radius=10)
        results_container.pack(fill="x", padx=24, pady=(4, 16))
        ctk.CTkLabel(
            results_container,
            text="Results (click to use host)",
            font=get_modern_font(10, "semibold"),
            text_color=ModernTheme.TEXT_SECONDARY,
        ).pack(anchor="w", padx=12, pady=(10, 6))
        
        self.discover_results = ctk.CTkFrame(results_container, fg_color="transparent")
        self.discover_results.pack(fill="x", padx=12, pady=(0, 12))
        
        # Log
        log_container = ctk.CTkFrame(discover_frame, fg_color=ModernTheme.BG_TERTIARY, corner_radius=10)
        log_container.pack(fill="x", padx=24, pady=(0, 20))
        ctk.CTkLabel(
            log_container,
            text="Discovery Log",
            font=get_modern_font(10, "semibold"),
            text_color=ModernTheme.TEXT_SECONDARY,
        ).pack(anchor="w", padx=12, pady=(10, 6))
        self.discover_log_box = ctk.CTkTextbox(
            log_container,
            fg_color=ModernTheme.BG_TERTIARY,
            text_color=ModernTheme.TEXT_PRIMARY,
            corner_radius=8,
            wrap="word",
            height=120,
        )
        self.discover_log_box.pack(fill="x", padx=12, pady=(0, 12))
        self.discover_log_box.configure(state="disabled")
        
        # Internal state
        self._discover_cancel_event = None
        self._discover_thread = None
        self._discover_current_total = 0
        self._discover_current_done = 0
        
        # Prefill
        self._discover_prefill_networks()

    def _discover_prefill_networks(self):
        nets = detect_local_networks()
        if nets:
            first = f"{nets[0].network_address}/{nets[0].prefixlen}"
            self.discover_subnet_entry.delete(0, "end")
            self.discover_subnet_entry.insert(0, first)
            self._discover_log(f"Detected {len(nets)} network(s). Using {first}")
        else:
            self._discover_log("No local networks detected; enter a subnet manually.")

    def _discover_set_running(self, running: bool):
        self.discover_start_btn.configure(state="disabled" if running else "normal")
        self.discover_stop_btn.configure(state="normal" if running else "disabled")

    def _start_discover(self):
        if self._discover_thread and self._discover_thread.is_alive():
            return
        self._discover_cancel_event = threading.Event()
        self._discover_set_running(True)
        self._discover_reset_progress()
        self._discover_clear_results()
        self._discover_log("Starting discovery...")
        self._update_status("Starting discovery", ModernTheme.STATUS_CONNECTING)

        def ui(cb):
            try:
                self.window.after(0, cb)
            except Exception:
                cb()

        mode = self.discover_mode_var.get()
        if mode == "broadcast":
            def worker():
                try:
                    def on_log(msg: str):
                        ui(lambda: self._discover_log(msg))

                    def on_found(ip: str, hostname: str, ssh_port: int):
                        ui(lambda: self._add_discovered_host(ip, f"beacon:{ssh_port}", f"{hostname}"))
                        ui(lambda: self._discover_log(f"BEACON {hostname} @ {ip}:{ssh_port}"))

                    listen_for_beacons(
                        on_log=on_log,
                        on_found=on_found,
                        stop_event=self._discover_cancel_event,
                        timeout_s=None,
                    )
                finally:
                    ui(lambda: self._discover_set_running(False))
                    self._update_status("Listening stopped", ModernTheme.STATUS_CONNECTED)

            self._discover_thread = threading.Thread(target=worker, daemon=True)
            self._discover_thread.start()
            return

        # Port scan mode
        subnet = self.discover_subnet_entry.get().strip()
        def worker():
            try:
                if subnet:
                    try:
                        net = ipaddress.IPv4Network(subnet, strict=False)
                    except Exception:
                        ui(lambda: self._discover_log(f"Invalid subnet: {subnet}"))
                        ui(lambda: self._discover_set_running(False))
                        self._update_status("Invalid subnet", ModernTheme.STATUS_DISCONNECTED)
                        return

                    def on_log(msg: str):
                        ui(lambda: self._discover_log(msg))

                    def on_progress(done: int, total: int):
                        ui(lambda: self._update_discover_progress(done, total, f"Scanning {subnet}"))

                    def on_found(host: str, banner: Optional[str]):
                        ui(lambda: self._add_discovered_host(host, str(net), banner))
                        ui(lambda: self._discover_log(f"FOUND {host} {('- ' + banner) if banner else ''}"))

                    scan_network(
                        net,
                        cancel_event=self._discover_cancel_event,
                        on_log=on_log,
                        on_progress=on_progress,
                        on_found=on_found,
                    )
                else:
                    def on_log(msg: str):
                        ui(lambda: self._discover_log(msg))

                    def on_progress(cidr: str, done: int, total: int):
                        ui(lambda: self._update_discover_progress(done, total, f"Scanning {cidr}"))

                    def on_found(cidr: str, host: str, banner: Optional[str]):
                        ui(lambda: self._add_discovered_host(host, cidr, banner))
                        ui(lambda: self._discover_log(f"FOUND {host} in {cidr} {('- ' + banner) if banner else ''}"))

                    discover_all_local(
                        cancel_event=self._discover_cancel_event,
                        on_log=on_log,
                        on_progress=on_progress,
                        on_found=on_found,
                    )
            finally:
                ui(lambda: self._discover_set_running(False))
                self._update_status("Discovery finished", ModernTheme.STATUS_CONNECTED)

        self._discover_thread = threading.Thread(target=worker, daemon=True)
        self._discover_thread.start()

    def _stop_discover(self):
        if self._discover_cancel_event:
            self._discover_cancel_event.set()
            self._discover_log("Stopping scan...")
            self._update_status("Stopping scan", ModernTheme.STATUS_WARNING)

    def _discover_reset_progress(self):
        self._discover_current_done = 0
        self._discover_current_total = 0
        self.discover_progress.set(0)
        self.discover_progress_label.configure(text="Idle")

    def _update_discover_progress(self, done: int, total: int, prefix: str):
        self._discover_current_done = done
        self._discover_current_total = total
        frac = (done / total) if total else 0.0
        self.discover_progress.set(frac)
        self.discover_progress_label.configure(text=f"{prefix}: {done}/{total}")

    def _discover_clear_results(self):
        for child in list(self.discover_results.winfo_children()):
            try:
                child.destroy()
            except Exception:
                pass

    def _add_discovered_host(self, host: str, cidr: str, banner: Optional[str]):
        row = ctk.CTkFrame(self.discover_results, fg_color="transparent")
        row.pack(fill="x", pady=2)
        text = f"{host}  ({cidr})"
        if banner:
            text += f"  - {banner}"
        btn = ctk.CTkButton(
            row,
            text=text,
            command=lambda: self._use_discovered_host(host),
            height=30,
            font=get_modern_font(10),
            **get_button_style("outline"),
        )
        btn.pack(fill="x")

    def _use_discovered_host(self, host: str):
        self.host_entry.delete(0, "end")
        self.host_entry.insert(0, host)
        self._update_status(f"Host set to {host}", ModernTheme.TEXT_INFO)

    def _discover_log(self, message: str):
        self.discover_log_box.configure(state="normal")
        self.discover_log_box.insert("end", message + "\n")
        self.discover_log_box.see("end")
        self.discover_log_box.configure(state="disabled")
    
    def _add_tooltips(self):
        """Add tooltips to UI elements"""
        try:
            from ui.theme import create_tooltip
            create_tooltip(self.load_button, "Load selected profile (Ctrl+L)")
            create_tooltip(self.save_button, "Save current connection as profile (Ctrl+S)")
            create_tooltip(self.delete_button, "Delete selected profile")
            create_tooltip(self.connect_button, "Connect to SSH server (Enter)")
            create_tooltip(self.host_entry, "Enter hostname or IP address")
            create_tooltip(self.port_entry, "SSH port (default: 22)")
        except Exception:
            pass  # Tooltips are optional
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for better UX"""
        # Ctrl+S to save profile
        self.window.bind("<Control-s>", lambda e: self._save_current_profile())
        # Ctrl+L to load profile
        self.window.bind("<Control-l>", lambda e: self._load_selected_profile())
        # Escape to clear form
        self.window.bind("<Escape>", lambda e: self._clear_form())
    
    def _load_profiles(self):
        """Load saved profiles into dropdown"""
        # Prefer most recently used order
        profiles = self.profile_manager.list_profiles_by_recent()
        profile_list = ["New Connection"] + profiles
        self.profile_dropdown.configure(values=profile_list)
        # Auto-select most recently used profile if available
        most_recent = self.profile_manager.get_most_recent_profile_name()
        if most_recent:
            self.profile_var.set(most_recent)
            self._load_selected_profile()
    
    def _on_profile_selected(self, profile_name):
        """Handle profile selection"""
        if profile_name != "New Connection":
            self._load_selected_profile()
    
    def _load_selected_profile(self):
        """Load selected profile data"""
        profile_name = self.profile_var.get()
        if profile_name == "New Connection":
            return
        
        profile = self.profile_manager.get_profile(profile_name)
        if profile:
            self.host_entry.delete(0, "end")
            self.host_entry.insert(0, profile.get("host", ""))
            
            self.username_entry.delete(0, "end")
            self.username_entry.insert(0, profile.get("username", ""))
            
            self.password_entry.delete(0, "end")
            self.password_entry.insert(0, profile.get("password", ""))
            
            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, str(profile.get("port", 22)))
            
            self._update_status(f"Loaded profile: {profile_name}")
    
    def _save_current_profile(self):
        """Save current connection as profile"""
        name = ctk.CTkInputDialog(
            text="Enter profile name:",
            title="Save Profile"
        ).get_input()
        
        if not name:
            return
        
        host = self.host_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
        port = self.port_entry.get()
        
        if not all([host, username, password]):
            messagebox.showerror("Error", "Please fill in all required fields")
            return
        
        try:
            port = int(port) if port else 22
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
            return
        
        if self.profile_manager.save_profile(name, host, username, password, port):
            self._load_profiles()
            self.profile_var.set(name)
            self._update_status(f"Profile '{name}' saved successfully")
        else:
            messagebox.showerror("Error", "Failed to save profile")
    
    def _delete_selected_profile(self):
        """Delete selected profile"""
        profile_name = self.profile_var.get()
        if profile_name == "New Connection":
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete profile '{profile_name}'?"):
            if self.profile_manager.delete_profile(profile_name):
                self._load_profiles()
                self.profile_var.set("New Connection")
                self._clear_form()
                self._update_status(f"Profile '{profile_name}' deleted")
            else:
                messagebox.showerror("Error", "Failed to delete profile")
    
    def _clear_form(self):
        """Clear the connection form"""
        self.host_entry.delete(0, "end")
        self.username_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.port_entry.delete(0, "end")
    
    def _connect(self):
        """Attempt SSH connection"""
        host = self.host_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        port_str = self.port_entry.get().strip()

        print(f"Debug: Host={host}, Username={username}, Password={'*' * len(password) if password else 'EMPTY'}")

        if not all([host, username, password]):
            messagebox.showerror("Error", "Please fill in all required fields")
            return

        try:
            port = int(port_str) if port_str else 22
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
            return

        # Update UI for connection attempt
        self.connect_button.configure(text="⏳ Connecting...", state="disabled")
        self._update_status("Connecting to server...", ModernTheme.STATUS_CONNECTING)

        def handle_connection_success(connected, message):
            if connected:
                self._update_status("✓ Connected successfully!", ModernTheme.STATUS_CONNECTED)
                # Mark profile as used if it is a saved profile
                selected = self.profile_var.get()
                if selected and selected != "New Connection":
                    self.profile_manager.mark_profile_used(selected)
                if self.on_connect_callback:
                    self.on_connect_callback(self.ssh_manager, host, username, port)
                self.window.destroy()
            else:
                self._update_status("✗ Connection failed", ModernTheme.STATUS_DISCONNECTED)
                self.connect_button.configure(text="⚡ Connect to Server", state="normal")

        def handle_error(error_message):
            self._update_status(f"✗ Error: {error_message}", ModernTheme.TEXT_ERROR)
            self.connect_button.configure(text="⚡ Connect to Server", state="normal")

        def on_connection_success_from_thread(connected, message):
            self.window.after(0, handle_connection_success, connected, message)

        def on_error_from_thread(error_message):
            self.window.after(0, handle_error, error_message)

        self.ssh_manager.set_connection_callbacks(on_connection_success_from_thread, on_error_from_thread)

        # Attempt connection in a separate thread
        import threading
        def connect_thread():
            self.ssh_manager.connect(host, username, password, port)

        threading.Thread(target=connect_thread, daemon=True).start()
    
    def _update_status(self, message: str, color: str = None):
        """Update status label and indicator"""
        self.status_label.configure(text=message)
        if color:
            self.status_label.configure(text_color=color)
            self.status_indicator.configure(text_color=color)
        else:
            self.status_label.configure(text_color=ModernTheme.TEXT_MUTED)
            self.status_indicator.configure(text_color=ModernTheme.STATUS_IDLE)
    
    def run(self):
        """Run the login window"""
        self.window.mainloop()
    
    def destroy(self):
        """Destroy the login window"""
        if self.window:
            self.window.destroy()
