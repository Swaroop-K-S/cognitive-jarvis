import customtkinter as ctk
import threading
from jarvis.ui.theme import COLORS, FONTS

class WebPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Web View / Status expands
        
        self._create_header()
        self._create_nav_bar()
        self._create_status_area()
        self._create_bookmarks()
        
    def _create_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        ctk.CTkLabel(head, text="🌐 NEURAL WEB LINK", font=FONTS["h2"], text_color=COLORS["text_dim"]).pack(side="left")

    def _create_nav_bar(self):
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        # Back Button
        ctk.CTkButton(nav, text="⬅", width=40, font=FONTS["body_bold"], fg_color=COLORS["bg_card"], 
                     command=lambda: self.run_web("back")).pack(side="left", padx=(0, 10))
        
        # URL Entry
        self.url_entry = ctk.CTkEntry(nav, placeholder_text="https://...", height=40, font=FONTS["body"])
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.url_entry.bind("<Return>", lambda e: self.run_web("go"))
        
        # Go Button
        ctk.CTkButton(nav, text="GO", width=60, font=FONTS["body_bold"], fg_color=COLORS["accent"], 
                     command=lambda: self.run_web("go")).pack(side="left", padx=5)
        
        # Scan Button
        ctk.CTkButton(nav, text="📷 SCAN PAGE", width=100, font=FONTS["body_bold"], fg_color=COLORS["text_dim"], 
                     command=lambda: self.run_web("snap")).pack(side="left", padx=5)

    def _create_status_area(self):
        # Status "Console"
        self.status_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=10)
        self.status_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.status_frame.pack_propagate(False)
        
        self.lbl_status = ctk.CTkLabel(self.status_frame, text="Browser Ready. Waiting for connection...", 
                                      text_color=COLORS["text_dim"], font=FONTS["body"], wraplength=600)
        self.lbl_status.pack(expand=True)

    def _create_bookmarks(self):
        bookmarks = ctk.CTkFrame(self, fg_color="transparent")
        bookmarks.grid(row=3, column=0, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(bookmarks, text="QUICK LINKS:", font=FONTS["tiny"], text_color=COLORS["text_dim"]).pack(side="left", padx=10)
        
        links = [
            ("Google", "google.com"), 
            ("GitHub", "github.com"), 
            ("YouTube", "youtube.com"), 
            ("News", "bbc.com")
        ]
        
        for name, url in links:
            ctk.CTkButton(bookmarks, text=name, width=80, height=30, fg_color=COLORS["bg_card"], hover_color=COLORS["accent_dim"],
                         command=lambda u=url: self.run_web("go", u)).pack(side="left", padx=5)

    def run_web(self, action, override_url=None):
        def _t():
            from jarvis.tools.web_automation import navigate_to, go_back, take_page_screenshot, get_current_url
            
            res = ""
            self.after(0, lambda: self.lbl_status.configure(text=f"Executing: {action.upper()}...", text_color=COLORS["accent"]))
            
            try:
                if action == "go":
                    url = override_url if override_url else self.url_entry.get()
                    res = navigate_to(url)
                elif action == "back":
                    res = go_back()
                elif action == "snap":
                    res = take_page_screenshot()
                    if "✓" in res:
                        # Could show preview here similar to vision page
                        pass
                
                curr = get_current_url()
                display = f"Current: {curr}\nResult: {res}"
                self.after(0, lambda: self.lbl_status.configure(text=display, text_color=COLORS["text_main"]))
                
            except Exception as e:
                self.after(0, lambda: self.lbl_status.configure(text=f"Error: {e}", text_color=COLORS["text_error"]))
            
        threading.Thread(target=_t, daemon=True).start()
