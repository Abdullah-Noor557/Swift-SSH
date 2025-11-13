"""
Discover panel UI for scanning local networks for open SSH servers.
"""

import customtkinter as ctk
import ipaddress
import threading
from typing import Callable, Optional

from ui.theme import ModernTheme, get_button_style, get_modern_font
from core.network_discovery import (
    detect_local_networks,
    discover_all_local,
    scan_network,
)


class DiscoverPanel:
    def __init__(self, parent, status_callback: Optional[Callable[[str, str], None]] = None):
        self.parent = parent
        self.status_callback = status_callback
        self.cancel_event = None
        self.scan_thread: Optional[threading.Thread] = None
        self.current_total = 0
        self.current_done = 0

        self._build_ui()
        self._prefill_networks()

    def _build_ui(self):
        root = ctk.CTkFrame(self.parent, fg_color=ModernTheme.BG_PRIMARY)
        root.pack(fill="both", expand=True)

        # Controls area
        controls = ctk.CTkFrame(root, fg_color=ModernTheme.BG_CARD)
        controls.pack(fill="x", padx=16, pady=16)

        # Network selection
        left = ctk.CTkFrame(controls, fg_color="transparent")
        left.pack(side="left", padx=8, pady=12)

        ctk.CTkLabel(
            left,
            text="Subnet (CIDR)",
            font=get_modern_font(10, "semibold"),
            text_color=ModernTheme.TEXT_SECONDARY,
        ).pack(anchor="w")

        entry_frame = ctk.CTkFrame(left, fg_color=ModernTheme.BG_TERTIARY, corner_radius=8)
        entry_frame.pack(fill="x")
        self.subnet_entry = ctk.CTkEntry(
            entry_frame,
            placeholder_text="auto-detect (leave empty to scan all local)",
            fg_color=ModernTheme.BG_TERTIARY,
            border_color=ModernTheme.BG_TERTIARY,
            text_color=ModernTheme.TEXT_PRIMARY,
            font=get_modern_font(10),
            width=320,
        )
        self.subnet_entry.pack(side="left", padx=8, pady=8)

        detect_style = get_button_style("secondary")
        self.detect_btn = ctk.CTkButton(
            entry_frame,
            text="Detect",
            command=self._prefill_networks,
            height=30,
            width=80,
            font=get_modern_font(10, "semibold"),
            **detect_style,
        )
        self.detect_btn.pack(side="left", padx=(8, 8))

        # Action buttons
        right = ctk.CTkFrame(controls, fg_color="transparent")
        right.pack(side="right", padx=8, pady=12)

        primary = get_button_style("primary")
        danger = get_button_style("danger")
        self.start_btn = ctk.CTkButton(
            right,
            text="Start Scan",
            command=self._start_scan,
            height=36,
            width=120,
            font=get_modern_font(11, "semibold"),
            **primary,
        )
        self.start_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = ctk.CTkButton(
            right,
            text="Stop",
            command=self._stop_scan,
            height=36,
            width=90,
            font=get_modern_font(11, "semibold"),
            state="disabled",
            **danger,
        )
        self.stop_btn.pack(side="left")

        # Progress area
        progress_frame = ctk.CTkFrame(root, fg_color=ModernTheme.BG_CARD)
        progress_frame.pack(fill="x", padx=16, pady=(0, 12))

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Idle",
            font=get_modern_font(10),
            text_color=ModernTheme.TEXT_SECONDARY,
        )
        self.progress_label.pack(anchor="w", padx=12, pady=(10, 4))

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=10,
            progress_color=ModernTheme.ACCENT_PRIMARY,
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=12, pady=(0, 12))

        # Log area
        log_frame = ctk.CTkFrame(root, fg_color=ModernTheme.BG_CARD)
        log_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        ctk.CTkLabel(
            log_frame,
            text="Discovery Log",
            font=get_modern_font(11, "bold"),
            text_color=ModernTheme.TEXT_PRIMARY,
        ).pack(anchor="w", padx=12, pady=(12, 6))

        self.log_box = ctk.CTkTextbox(
            log_frame,
            fg_color=ModernTheme.BG_TERTIARY,
            text_color=ModernTheme.TEXT_PRIMARY,
            corner_radius=8,
            wrap="word",
        )
        self.log_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.log_box.configure(state="disabled")

    def _prefill_networks(self):
        nets = detect_local_networks()
        if nets:
            first = f"{nets[0].network_address}/{nets[0].prefixlen}"
            self.subnet_entry.delete(0, "end")
            self.subnet_entry.insert(0, first)
            self._log(f"Detected {len(nets)} network(s). Using {first} by default.")
        else:
            self._log("No local networks detected. Enter a subnet, e.g., 192.168.1.0/24")

    def _set_running(self, running: bool):
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")

    def _start_scan(self):
        if self.scan_thread and self.scan_thread.is_alive():
            return
        subnet = self.subnet_entry.get().strip()
        self.cancel_event = threading.Event()
        self._set_running(True)
        self._reset_progress()
        self._log("Starting discovery...")
        self._status("Starting discovery", "loading")

        def worker():
            try:
                if subnet:
                    try:
                        net = ipaddress.IPv4Network(subnet, strict=False)
                    except Exception:
                        self._ui(lambda: self._log(f"Invalid subnet: {subnet}"))
                        self._ui(lambda: self._set_running(False))
                        self._status("Invalid subnet", "error")
                        return

                    def on_log(msg: str):
                        self._ui(lambda: self._log(msg))

                    def on_progress(done: int, total: int):
                        self._ui(lambda: self._update_progress(done, total, f"Scanning {subnet}"))

                    def on_found(host: str, banner: Optional[str]):
                        self._ui(lambda: self._log(f"FOUND {host} {('- ' + banner) if banner else ''}"))

                    scan_network(
                        net,
                        cancel_event=self.cancel_event,
                        on_log=on_log,
                        on_progress=on_progress,
                        on_found=on_found,
                    )
                else:
                    def on_log(msg: str):
                        self._ui(lambda: self._log(msg))

                    def on_progress(cidr: str, done: int, total: int):
                        self._ui(lambda: self._update_progress(done, total, f"Scanning {cidr}"))

                    def on_found(cidr: str, host: str, banner: Optional[str]):
                        self._ui(lambda: self._log(f"FOUND {host} in {cidr} {('- ' + banner) if banner else ''}"))

                    discover_all_local(
                        cancel_event=self.cancel_event,
                        on_log=on_log,
                        on_progress=on_progress,
                        on_found=on_found,
                    )
            finally:
                self._ui(lambda: self._set_running(False))
                self._status("Discovery finished", "success")

        self.scan_thread = threading.Thread(target=worker, daemon=True)
        self.scan_thread.start()

    def _stop_scan(self):
        if self.cancel_event:
            self.cancel_event.set()
            self._log("Stopping scan...")
            self._status("Stopping scan", "warning")

    def _reset_progress(self):
        self.current_done = 0
        self.current_total = 0
        self.progress_bar.set(0)
        self.progress_label.configure(text="Idle")

    def _update_progress(self, done: int, total: int, prefix: str):
        self.current_done = done
        self.current_total = total
        frac = (done / total) if total else 0.0
        self.progress_bar.set(frac)
        self.progress_label.configure(text=f"{prefix}: {done}/{total}")

    def _log(self, message: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _ui(self, fn):
        try:
            self.log_box.after(0, fn)
        except Exception:
            fn()

    def _status(self, message: str, status_type: str):
        if self.status_callback:
            try:
                self.status_callback(message, status_type)
            except Exception:
                pass


