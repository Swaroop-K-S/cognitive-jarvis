import customtkinter as ctk
from jarvis.ui.theme import COLORS, FONTS

class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, navigate_callback, current_page="chat"):
        super().__init__(parent, width=220, corner_radius=0, fg_color=COLORS["bg_sidebar"])
        self.navigate_callback = navigate_callback
        self.current_page = current_page
        
        self.grid_rowconfigure(10, weight=1)
        
        self._create_header()
        self._create_nav_items()
        self._create_footer()
        
    def _create_header(self):
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=(40, 20), sticky="ew")
        
        # BRO (Blue/Teal) AI (White)
        ctk.CTkLabel(title_frame, text="BRO", font=("Segoe UI", 32, "bold"), text_color=COLORS["accent"]).pack(side="left")
        ctk.CTkLabel(title_frame, text="AI", font=("Segoe UI", 32, "bold"), text_color=COLORS["text_main"]).pack(side="left", padx=5)
        
        # Status
        status = ctk.CTkLabel(self, text="● ONLINE", font=("Segoe UI", 10, "bold"), text_color=COLORS["text_success"])
        status.grid(row=1, column=0, padx=20, pady=(0, 30), sticky="w")

    def _create_nav_items(self):
        self.buttons = {}
        items = [
            ("💬  Chat", "chat"),
            ("📈  Dashboard", "dashboard"),
            ("👁️  Vision", "vision"),
            ("🌐  Web Browser", "web"),
            ("📅  Calendar", "calendar"),
            ("🛒  Shopping", "shopping"),
            ("📱  Phone Control", "phone"),
            ("📝  Notes & Tasks", "notes"),
            ("🎵  Music Player", "music"),
            ("⚙️  Settings", "settings"),
        ]
        
        for i, (txt, key) in enumerate(items):
            btn = ctk.CTkButton(
                self, 
                text=txt, 
                font=FONTS["body"], 
                fg_color="transparent", 
                text_color=COLORS["text_dim"],
                hover_color=COLORS["bg_card"],
                anchor="w",
                height=45,
                corner_radius=8,
                command=lambda k=key: self.navigate(k)
            )
            btn.grid(row=i+2, column=0, padx=12, pady=2, sticky="ew")
            self.buttons[key] = btn
            
        self.highlight_nav(self.current_page)

    def _create_footer(self):
        # Mini Mode Toggle
        mini_btn = ctk.CTkButton(self, text="📱 Mini View", fg_color=COLORS["bg_card"], 
                                 hover_color=COLORS["glass_border"],
                                 font=FONTS["tiny"], height=30,
                                 command=lambda: self.navigate_callback("mini_mode"))
        mini_btn.grid(row=11, column=0, padx=20, pady=20, sticky="ew")

    def navigate(self, page_name):
        self.navigate_callback(page_name)
        self.highlight_nav(page_name)

    def highlight_nav(self, page_name):
        for key, btn in self.buttons.items():
            if key == page_name:
                btn.configure(fg_color=COLORS["bg_card"], text_color=COLORS["accent"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_dim"])
