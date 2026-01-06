import customtkinter as ctk
from jarvis.ui.theme import COLORS, FONTS, apply_theme

class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=1)
        
        self._create_header()
        self._create_sections()
        
    def _create_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        ctk.CTkLabel(head, text="⚙️ SYSTEM CONTROL", font=FONTS["h2"], text_color=COLORS["text_dim"]).pack(side="left")
        
    def _create_sections(self):
        # AI Brain Settings
        self._create_section("🧠 Neural Engine", [
            ("Model", ["llama3.1", "mistral", "gemma:2b"], "llama3.1"),
            ("Temperature", ["0.1 (Precise)", "0.7 (Creative)", "0.9 (Wild)"], "0.7 (Creative)"),
        ], row=1)
        
        # Voice Settings
        self._create_section("🗣️ Voice Synthesis", [
            ("Persona", ["Jarvis (Matthew)", "Friday (Salli)", "GLaDOS"], "Jarvis (Matthew)"),
            ("Speed", ["0.8x", "1.0x", "1.2x"], "1.0x"),
            ("Device", ["Default Output", "Headphones"], "Default Output"),
        ], row=2)
        
        # UI Settings
        self._create_section("🎨 Interface", [
            ("Theme", ["Midnight Teal", "Cyber Punk", "Clean White"], "Midnight Teal"),
            ("Font Size", ["Small", "Medium", "Large"], "Medium"),
        ], row=3)
        
    def _create_section(self, title, options, row):
        frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"])
        frame.grid(row=row, column=0, sticky="ew", padx=20, pady=10)
        
        ctk.CTkLabel(frame, text=title, font=FONTS["h3"], text_color=COLORS["accent"]).pack(anchor="w", padx=20, pady=(15, 10))
        
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="x", padx=20, pady=(0, 20))
        
        for i, (label, choices, default) in enumerate(options):
            row_frame = ctk.CTkFrame(content, fg_color="transparent")
            row_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(row_frame, text=label, font=FONTS["body"], width=100, anchor="w").pack(side="left")
            
            var = ctk.StringVar(value=default)
            menu = ctk.CTkOptionMenu(row_frame, values=choices, variable=var,
                                     width=200, fg_color=COLORS["bg_dark"], button_color=COLORS["accent"],
                                     command=lambda v, l=label: self.on_change(l, v))
            menu.pack(side="left", padx=20)
            
    def on_change(self, label, value):
        print(f"Setting Changed: {label} -> {value}")
        # Connect to actual backend config here using config.py
