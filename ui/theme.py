"""
Theme configuration for SwiftSSH with modern professional aesthetic
Refined dark theme with carefully balanced colors for optimal UX
"""

import customtkinter as ctk

# Color scheme - Modern professional dark theme with refined palette
class ModernTheme:
    # Background colors - Carefully layered depth
    BG_PRIMARY = "#0d1117"      # Deep background - GitHub-inspired
    BG_SECONDARY = "#161b22"    # Panel backgrounds
    BG_TERTIARY = "#1f2937"     # Elevated surfaces
    BG_HOVER = "#2d3748"        # Hover states
    BG_CARD = "#1a2332"         # Card backgrounds
    BG_INPUT = "#0d1421"        # Input field backgrounds
    
    # Accent colors - Vibrant yet professional
    ACCENT_PRIMARY = "#3b82f6"   # Modern blue - primary actions
    ACCENT_SECONDARY = "#8b5cf6" # Purple - secondary actions
    ACCENT_SUCCESS = "#10b981"   # Emerald green - success states
    ACCENT_WARNING = "#f59e0b"   # Amber - warnings
    ACCENT_ERROR = "#ef4444"     # Red - destructive actions
    ACCENT_INFO = "#06b6d4"      # Cyan - info states
    ACCENT_HIGHLIGHT = "#6366f1" # Indigo - highlights
    
    # Gradient colors for modern effects
    GRADIENT_START = "#3b82f6"
    GRADIENT_MID = "#8b5cf6"
    GRADIENT_END = "#06b6d4"
    
    # Text colors - Optimized for readability
    TEXT_PRIMARY = "#f9fafb"     # Almost white - high contrast
    TEXT_SECONDARY = "#d1d5db"   # Light gray
    TEXT_TERTIARY = "#9ca3af"    # Medium gray
    TEXT_MUTED = "#6b7280"       # Muted gray
    TEXT_DISABLED = "#4b5563"    # Disabled text
    
    # Status text colors
    TEXT_SUCCESS = "#34d399"     # Success text
    TEXT_WARNING = "#fbbf24"     # Warning text
    TEXT_ERROR = "#f87171"       # Error text
    TEXT_INFO = "#22d3ee"        # Info text
    
    # Border colors - Refined and subtle
    BORDER_PRIMARY = "#374151"   # Default border
    BORDER_SECONDARY = "#4b5563" # Secondary border
    BORDER_ACCENT = "#3b82f6"    # Accent border
    BORDER_SUBTLE = "#1f2937"    # Very subtle border
    BORDER_FOCUS = "#60a5fa"     # Focus state border
    
    # Status colors - Clear visual feedback
    STATUS_CONNECTED = "#10b981"
    STATUS_DISCONNECTED = "#ef4444"
    STATUS_CONNECTING = "#f59e0b"
    STATUS_IDLE = "#6b7280"
    STATUS_WARNING = "#f59e0b"
    
    # Terminal colors - Classic with modern twist
    TERMINAL_BG = "#0a0e14"
    TERMINAL_FG = "#00ff9f"
    TERMINAL_CURSOR = "#00d4ff"
    
    # Special UI elements
    SCROLLBAR_BG = "#1f2937"
    SCROLLBAR_FG = "#4b5563"
    TOOLTIP_BG = "#1f2937"
    TOOLTIP_BORDER = "#374151"
    
    # Shadows for depth (CSS-like values for reference)
    SHADOW_SM = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    SHADOW_MD = "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
    SHADOW_LG = "0 10px 15px -3px rgba(0, 0, 0, 0.1)"
    SHADOW_XL = "0 20px 25px -5px rgba(0, 0, 0, 0.1)"

# Keep backward compatibility
class HackerTheme(ModernTheme):
    pass

def apply_theme():
    """Apply the modern theme to CustomTkinter"""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Configure custom color scheme
    ctk.ThemeManager.theme["CTk"]["fg_color"] = [ModernTheme.BG_SECONDARY, ModernTheme.BG_SECONDARY]
    ctk.ThemeManager.theme["CTk"]["top_fg_color"] = [ModernTheme.BG_PRIMARY, ModernTheme.BG_PRIMARY]
    ctk.ThemeManager.theme["CTk"]["text_color"] = [ModernTheme.TEXT_PRIMARY, ModernTheme.TEXT_PRIMARY]
    ctk.ThemeManager.theme["CTk"]["text_color_disabled"] = [ModernTheme.TEXT_DISABLED, ModernTheme.TEXT_DISABLED]
    ctk.ThemeManager.theme["CTk"]["border_color"] = [ModernTheme.BORDER_PRIMARY, ModernTheme.BORDER_PRIMARY]
    
    # Button colors
    ctk.ThemeManager.theme["CTkButton"]["fg_color"] = [ModernTheme.ACCENT_PRIMARY, ModernTheme.ACCENT_PRIMARY]
    ctk.ThemeManager.theme["CTkButton"]["hover_color"] = [ModernTheme.ACCENT_HIGHLIGHT, ModernTheme.ACCENT_HIGHLIGHT]
    ctk.ThemeManager.theme["CTkButton"]["border_color"] = [ModernTheme.BORDER_ACCENT, ModernTheme.BORDER_ACCENT]
    ctk.ThemeManager.theme["CTkButton"]["text_color"] = [ModernTheme.TEXT_PRIMARY, ModernTheme.TEXT_PRIMARY]
    
    # Entry colors with improved focus states
    ctk.ThemeManager.theme["CTkEntry"]["fg_color"] = [ModernTheme.BG_INPUT, ModernTheme.BG_INPUT]
    ctk.ThemeManager.theme["CTkEntry"]["border_color"] = [ModernTheme.BORDER_PRIMARY, ModernTheme.BORDER_PRIMARY]
    ctk.ThemeManager.theme["CTkEntry"]["text_color"] = [ModernTheme.TEXT_PRIMARY, ModernTheme.TEXT_PRIMARY]
    
    # Frame colors
    ctk.ThemeManager.theme["CTkFrame"]["fg_color"] = [ModernTheme.BG_SECONDARY, ModernTheme.BG_SECONDARY]
    ctk.ThemeManager.theme["CTkFrame"]["border_color"] = [ModernTheme.BORDER_PRIMARY, ModernTheme.BORDER_PRIMARY]
    
    # Scrollbar colors
    ctk.ThemeManager.theme["CTkScrollbar"]["fg_color"] = [ModernTheme.SCROLLBAR_BG, ModernTheme.SCROLLBAR_BG]
    ctk.ThemeManager.theme["CTkScrollbar"]["button_color"] = [ModernTheme.SCROLLBAR_FG, ModernTheme.SCROLLBAR_FG]
    ctk.ThemeManager.theme["CTkScrollbar"]["button_hover_color"] = [ModernTheme.BORDER_PRIMARY, ModernTheme.BORDER_PRIMARY]

def get_terminal_style():
    """Get terminal-specific styling with caching"""
    cache_key = ("terminal",)
    if cache_key not in _style_cache:
        _style_cache[cache_key] = {
            "bg": ModernTheme.TERMINAL_BG,
            "fg": ModernTheme.TERMINAL_FG,
            "insertbackground": ModernTheme.TERMINAL_CURSOR,
            "font": ("Consolas", 11),
            "relief": "flat",
            "borderwidth": 0
        }
    return _style_cache[cache_key]

def create_tooltip(widget, text):
    """Create a modern tooltip for a widget"""
    tooltip = None
    
    def show_tooltip(event):
        nonlocal tooltip
        if tooltip:
            return
        
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25
        
        tooltip = ctk.CTkToplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
        
        label = ctk.CTkLabel(
            tooltip,
            text=text,
            fg_color=ModernTheme.TOOLTIP_BG,
            text_color=ModernTheme.TEXT_SECONDARY,
            corner_radius=6,
            font=("Segoe UI", 10)
        )
        label.pack(padx=8, pady=6)
    
    def hide_tooltip(event):
        nonlocal tooltip
        if tooltip:
            tooltip.destroy()
            tooltip = None
    
    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)

def get_file_icon_color(file_type):
    """Get appropriate icon color based on file type"""
    icon_colors = {
        "folder": ModernTheme.ACCENT_WARNING,
        "text": ModernTheme.TEXT_PRIMARY,
        "image": ModernTheme.ACCENT_SECONDARY,
        "archive": ModernTheme.ACCENT_INFO,
        "executable": ModernTheme.ACCENT_SUCCESS,
        "code": ModernTheme.ACCENT_PRIMARY,
        "default": ModernTheme.TEXT_SECONDARY
    }
    return icon_colors.get(file_type, icon_colors["default"])

def get_button_style(variant="primary"):
    """Get consistent button styling based on variant with caching"""
    cache_key = ("button", variant)
    if cache_key not in _style_cache:
        styles = {
            "primary": {
                "fg_color": ModernTheme.ACCENT_PRIMARY,
                "hover_color": ModernTheme.ACCENT_HIGHLIGHT,
                "text_color": ModernTheme.TEXT_PRIMARY,
                "border_width": 0,
                "corner_radius": 8
            },
            "secondary": {
                "fg_color": ModernTheme.ACCENT_SECONDARY,
                "hover_color": ModernTheme.GRADIENT_MID,
                "text_color": ModernTheme.TEXT_PRIMARY,
                "border_width": 0,
                "corner_radius": 8
            },
            "danger": {
                "fg_color": ModernTheme.ACCENT_ERROR,
                "hover_color": "#dc2626",
                "text_color": ModernTheme.TEXT_PRIMARY,
                "border_width": 0,
                "corner_radius": 8
            },
            "success": {
                "fg_color": ModernTheme.ACCENT_SUCCESS,
                "hover_color": "#059669",
                "text_color": ModernTheme.TEXT_PRIMARY,
                "border_width": 0,
                "corner_radius": 8
            },
            "ghost": {
                "fg_color": "transparent",
                "hover_color": ModernTheme.BG_HOVER,
                "text_color": ModernTheme.TEXT_SECONDARY,
                "border_width": 2,
                "border_color": ModernTheme.BORDER_PRIMARY,
                "corner_radius": 8
            },
            "outline": {
                "fg_color": "transparent",
                "hover_color": ModernTheme.BG_TERTIARY,
                "text_color": ModernTheme.TEXT_PRIMARY,
                "border_width": 2,
                "border_color": ModernTheme.ACCENT_PRIMARY,
                "corner_radius": 8
            }
        }
        _style_cache[cache_key] = styles.get(variant, styles["primary"])
    return _style_cache[cache_key]

def get_card_style():
    """Get consistent card/panel styling with caching"""
    cache_key = ("card",)
    if cache_key not in _style_cache:
        _style_cache[cache_key] = {
            "fg_color": ModernTheme.BG_CARD,
            "border_width": 1,
            "border_color": ModernTheme.BORDER_SUBTLE,
            "corner_radius": 12
        }
    return _style_cache[cache_key]

def get_input_style():
    """Get consistent input field styling with caching"""
    cache_key = ("input",)
    if cache_key not in _style_cache:
        _style_cache[cache_key] = {
            "fg_color": ModernTheme.BG_INPUT,
            "border_width": 2,
            "border_color": ModernTheme.BORDER_PRIMARY,
            "text_color": ModernTheme.TEXT_PRIMARY,
            "corner_radius": 8
        }
    return _style_cache[cache_key]

def get_header_style():
    """Get consistent header styling"""
    return {
        "fg_color": ModernTheme.BG_CARD,
        "border_width": 0,
        "corner_radius": 0
    }

def get_badge_style(variant="default"):
    """Get badge styling for status indicators"""
    badge_styles = {
        "default": {
            "fg_color": ModernTheme.BG_TERTIARY,
            "text_color": ModernTheme.TEXT_SECONDARY,
            "corner_radius": 12
        },
        "success": {
            "fg_color": ModernTheme.ACCENT_SUCCESS,
            "text_color": ModernTheme.TEXT_PRIMARY,
            "corner_radius": 12
        },
        "warning": {
            "fg_color": ModernTheme.ACCENT_WARNING,
            "text_color": ModernTheme.BG_PRIMARY,
            "corner_radius": 12
        },
        "error": {
            "fg_color": ModernTheme.ACCENT_ERROR,
            "text_color": ModernTheme.TEXT_PRIMARY,
            "corner_radius": 12
        },
        "info": {
            "fg_color": ModernTheme.ACCENT_INFO,
            "text_color": ModernTheme.TEXT_PRIMARY,
            "corner_radius": 12
        }
    }
    return badge_styles.get(variant, badge_styles["default"])

def get_status_color(status):
    """Get color for connection status"""
    status_colors = {
        "connected": ModernTheme.STATUS_CONNECTED,
        "disconnected": ModernTheme.STATUS_DISCONNECTED,
        "connecting": ModernTheme.STATUS_CONNECTING,
        "error": ModernTheme.TEXT_ERROR,
        "warning": ModernTheme.STATUS_WARNING,
        "idle": ModernTheme.STATUS_IDLE
    }
    return status_colors.get(status, ModernTheme.TEXT_MUTED)

# Performance optimization caches
_font_cache = {}
_style_cache = {}

def get_modern_font(size=11, weight="normal"):
    """Get modern font configuration with caching"""
    cache_key = (size, weight)
    if cache_key not in _font_cache:
        # Map weight names to font tuples
        if weight == "bold":
            _font_cache[cache_key] = ("Segoe UI", size, "bold")
        elif weight in ["semibold", "medium"]:
            _font_cache[cache_key] = ("Segoe UI Semibold", size)
        else:
            _font_cache[cache_key] = ("Segoe UI", size)
    return _font_cache[cache_key]

def get_icon_font(size=14):
    """Get emoji/icon font configuration with caching"""
    cache_key = ("icon", size)
    if cache_key not in _font_cache:
        _font_cache[cache_key] = ("Segoe UI Emoji", size)
    return _font_cache[cache_key]
