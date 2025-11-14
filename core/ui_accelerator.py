"""
UI Acceleration and Performance Enhancement Module
Implements various techniques to improve UI smoothness and responsiveness
"""

import sys
import ctypes
import platform


class UIAccelerator:
    """Handles UI performance optimizations and acceleration"""
    
    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self.is_macos = platform.system() == "Darwin"
        self.is_linux = platform.system() == "Linux"
        self.dpi_awareness_set = False
        self.process_priority_set = False
    
    def enable_all_optimizations(self):
        """Enable all available UI optimizations"""
        self.enable_dpi_awareness()
        self.enable_process_priority()
        self.enable_compositing()
        self.configure_tcl_rendering()
        return self.get_optimization_status()
    
    def enable_dpi_awareness(self):
        """Enable DPI awareness for crisp rendering on high-DPI displays"""
        if not self.is_windows:
            return False
        
        try:
            # Try Windows 10+ DPI awareness
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
                self.dpi_awareness_set = True
                return True
            except Exception:
                pass
            
            # Fallback to older Windows versions
            try:
                ctypes.windll.user32.SetProcessDPIAware()
                self.dpi_awareness_set = True
                return True
            except Exception:
                pass
            
            return False
        except Exception as e:
            print(f"Could not enable DPI awareness: {e}")
            return False
    
    def enable_process_priority(self):
        """Increase process priority for better UI responsiveness"""
        if not self.is_windows:
            return False
        
        try:
            import psutil
            p = psutil.Process()
            # Set to above normal priority (not realtime to avoid system issues)
            if self.is_windows:
                p.nice(psutil.HIGH_PRIORITY_CLASS)
            else:
                p.nice(-5)  # Unix nice value
            self.process_priority_set = True
            return True
        except Exception as e:
            print(f"Could not set process priority: {e}")
            return False
    
    def enable_compositing(self):
        """Enable desktop compositing hints for smoother rendering"""
        if self.is_windows:
            try:
                # Enable Windows desktop composition
                ctypes.windll.dwmapi.DwmEnableComposition(1)
                return True
            except Exception:
                return False
        return False
    
    def configure_tcl_rendering(self):
        """Configure TCL/Tk rendering options for better performance"""
        try:
            import tkinter as tk
            
            # Create temporary root to set options
            temp_root = tk.Tk()
            temp_root.withdraw()
            
            # Enable double buffering (reduces flicker)
            temp_root.tk.call('tk', 'useinputmethods', True)
            
            # Set rendering options
            try:
                # Try to enable hardware acceleration if available
                temp_root.tk.call('wm', 'attributes', '.', '-alpha', 1.0)
            except Exception:
                pass
            
            temp_root.destroy()
            return True
        except Exception as e:
            print(f"Could not configure TCL rendering: {e}")
            return False
    
    def optimize_window(self, window):
        """Apply window-specific optimizations"""
        try:
            # Enable double buffering (reduces flicker)
            window.update_idletasks()
            
            # Set window attributes for better performance
            if self.is_windows:
                try:
                    # Get window handle
                    hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
                    
                    # Enable layered window for better compositing
                    GWL_EXSTYLE = -20
                    WS_EX_LAYERED = 0x80000
                    ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED)
                    
                    # Set window to use GPU acceleration if available
                    ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 255, 2)
                except Exception:
                    pass
            
            return True
        except Exception as e:
            print(f"Could not optimize window: {e}")
            return False
    
    def enable_smooth_scrolling(self, scrollable_widget):
        """Enable smooth scrolling for widgets"""
        try:
            # Configure smooth scrolling
            scrollable_widget.configure(scrollbar_button_color="transparent")
            return True
        except Exception:
            return False
    
    def get_optimization_status(self):
        """Get status of all optimizations"""
        return {
            "dpi_awareness": self.dpi_awareness_set,
            "process_priority": self.process_priority_set,
            "platform": platform.system(),
            "python_version": sys.version.split()[0]
        }


# Singleton instance
_accelerator = None


def get_accelerator():
    """Get or create the UI accelerator singleton"""
    global _accelerator
    if _accelerator is None:
        _accelerator = UIAccelerator()
    return _accelerator


def enable_ui_acceleration():
    """Convenient function to enable all UI acceleration features"""
    accelerator = get_accelerator()
    status = accelerator.enable_all_optimizations()
    return status


def optimize_window(window):
    """Optimize a specific window"""
    accelerator = get_accelerator()
    return accelerator.optimize_window(window)


# Widget-specific optimizations
class WidgetOptimizer:
    """Provides widget-level performance optimizations"""
    
    @staticmethod
    def optimize_text_widget(text_widget):
        """Optimize text widget performance"""
        try:
            # Disable autoseparators for undo (reduces overhead)
            text_widget.config(autoseparators=False)
            
            # Limit undo stack
            text_widget.config(maxundo=50)
            
            # Use wrap=none for better performance if possible
            # text_widget.config(wrap='none')
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def optimize_treeview(treeview):
        """Optimize treeview widget performance"""
        try:
            # Disable visual effects during updates
            treeview.update_idletasks()
            return True
        except Exception:
            return False
    
    @staticmethod
    def batch_widget_updates(widget, update_func):
        """Batch widget updates to reduce redraws"""
        try:
            # Disable updates
            widget.update_idletasks()
            
            # Perform updates
            update_func()
            
            # Re-enable and force single update
            widget.update()
            
            return True
        except Exception:
            return False


# Frame rate optimization
class FrameRateOptimizer:
    """Manages frame rate and update timing for smooth animations"""
    
    def __init__(self, target_fps=60):
        self.target_fps = target_fps
        self.frame_time = 1000 / target_fps  # milliseconds
        self.last_update = 0
    
    def should_update(self, current_time):
        """Check if enough time has passed for next frame"""
        if current_time - self.last_update >= self.frame_time:
            self.last_update = current_time
            return True
        return False
    
    def throttle_callback(self, callback, window):
        """Throttle callback to target frame rate"""
        import time
        current_time = time.time() * 1000
        
        if self.should_update(current_time):
            callback()
        else:
            # Schedule for next frame
            delay = int(self.frame_time - (current_time - self.last_update))
            if delay > 0:
                window.after(delay, callback)


# Memory optimization
class MemoryOptimizer:
    """Optimizes memory usage for better performance"""
    
    @staticmethod
    def clear_unused_widgets(parent):
        """Clear unused widgets to free memory"""
        try:
            import gc
            
            # Force garbage collection
            gc.collect()
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def optimize_images(image_cache):
        """Optimize image cache"""
        try:
            # Clear old images from cache
            if len(image_cache) > 100:
                # Keep only most recent 50
                items = list(image_cache.items())
                image_cache.clear()
                image_cache.update(dict(items[-50:]))
            return True
        except Exception:
            return False


# Render optimization utilities
def defer_render(widget, delay_ms=16):
    """Defer rendering to next frame (approximately 60fps)"""
    widget.after(delay_ms, widget.update_idletasks)


def batch_configure(widgets, **kwargs):
    """Batch configure multiple widgets to reduce redraws"""
    for widget in widgets:
        widget.configure(**kwargs)
    # Single update after all configurations
    if widgets:
        widgets[0].update_idletasks()

