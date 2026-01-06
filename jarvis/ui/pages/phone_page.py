import customtkinter as ctk
from jarvis.ui.theme import COLORS, FONTS

class PhonePage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=1) # Recent
        self.grid_columnconfigure(1, weight=1) # Dialer
        self.grid_rowconfigure(0, weight=1)
        
        self._create_recents()
        self._create_dialer()
        
    def _create_recents(self):
        frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"])
        frame.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        
        ctk.CTkLabel(frame, text="📞 RECENT ACTIVITY", font=FONTS["h3"], text_color=COLORS["text_dim"]).pack(anchor="w", padx=20, pady=20)
        
        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Mock Calls
        calls = [
            ("Mom", "Mobile", "10:30 AM", "missed"),
            ("Boss", "Work", "Yesterday", "incoming"),
            ("Pizza Place", "Unknown", "Yesterday", "outgoing"),
            ("Scam Likely", "Unknown", "Monday", "blocked"),
        ]
        
        for name, label, time, type_ in calls:
            row = ctk.CTkFrame(scroll, fg_color="transparent", height=50)
            row.pack(fill="x", pady=5)
            
            icon = "↗️" if type_ == "outgoing" else "↙️"
            color = COLORS["text_success"]
            if type_ == "missed": 
                icon = "missed"
                color = COLORS["text_error"]
            elif type_ == "blocked":
                icon = "🚫"
                color = COLORS["text_dim"]
                
            ctk.CTkLabel(row, text=icon, width=30, text_color=color).pack(side="left", padx=5)
            
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(info, text=name, font=FONTS["body_bold"], text_color=COLORS["text_main"]).pack(anchor="w")
            ctk.CTkLabel(info, text=label, font=FONTS["tiny"], text_color=COLORS["text_dim"]).pack(anchor="w")
            
            ctk.CTkLabel(row, text=time, font=FONTS["tiny"], text_color=COLORS["text_dim"]).pack(side="right", padx=10)

    def _create_dialer(self):
        frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"])
        frame.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        
        # Display
        display = ctk.CTkEntry(frame, font=("Segoe UI", 32), justify="center", 
                               fg_color="transparent", border_width=0, placeholder_text="Enter Number")
        display.pack(fill="x", pady=(40, 20), padx=20)
        
        # Keypad
        pad = ctk.CTkFrame(frame, fg_color="transparent")
        pad.pack(expand=True)
        
        keys = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            ["*", "0", "#"]
        ]
        
        for r, row_keys in enumerate(keys):
            for c, key in enumerate(row_keys):
                btn = ctk.CTkButton(pad, text=key, width=70, height=70, corner_radius=35,
                                    fg_color=COLORS["bg_dark"], hover_color=COLORS["accent"],
                                    command=lambda k=key: display.insert("end", k),
                                    font=("Segoe UI", 24))
                btn.grid(row=r, column=c, padx=10, pady=10)
                
        # Call Button
        call_btn = ctk.CTkButton(frame, text="📞 CALL", width=200, height=50, corner_radius=25,
                                 fg_color=COLORS["text_success"], hover_color="#00EE00",
                                 font=FONTS["h3"])
        call_btn.pack(pady=40)
