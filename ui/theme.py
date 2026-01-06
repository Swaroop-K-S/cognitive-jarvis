# UI Theme Configuration: Midnight Teal & Neon
# Using CustomTkinter Color formatting

COLORS = {
    # Backgrounds
    "bg_dark": "#0D1117",       # Deepest Blue-Black (GitHub Dim/Midnight)
    "bg_card": "#161B22",       # Slightly lighter card background
    "bg_sidebar": "#090C10",    # Darkest sidebar
    
    # Accents (Neon Teal/Blue)
    "accent": "#00F0FF",        # Cyberpunk Cyan
    "accent_hover": "#00BCD4",  # Slightly dimmed cyan
    "accent_dim": "#1F6FEB",    # Classic Blue for secondary actions
    
    # Text
    "text_main": "#E6EDF3",     # White-ish
    "text_dim": "#8B949E",      # Gray text
    "text_success": "#2EA043",  # Green
    "text_error": "#F85149",    # Red
    
    # Special
    "glass_border": "#30363D",  # Subtle border
    "mic_active": "#00F0FF",    # Cyan for mic active
    "mic_inactive": "#F85149",  # Red for inactive
}

FONTS = {
    "h1": ("Segoe UI", 24, "bold"),
    "h2": ("Segoe UI", 18, "bold"),
    "body": ("Segoe UI", 14),
    "code": ("Consolas", 13),
    "tiny": ("Segoe UI", 10),
}

import customtkinter as ctk

def apply_theme(ctk_obj):
    """Apply global theme settings."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    # You can apply object specific settings here if needed
    pass
