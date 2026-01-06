import customtkinter as ctk
from datetime import datetime
import calendar
from jarvis.ui.theme import COLORS, FONTS

class CalendarPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.current_date = datetime.now()
        self.year = self.current_date.year
        self.month = self.current_date.month
        
        self.grid_columnconfigure(0, weight=2) # Calendar Grid
        self.grid_columnconfigure(1, weight=1) # Event List
        self.grid_rowconfigure(0, weight=1)
        
        self._create_calendar_view()
        self._create_event_sidebar()
        
    def _create_calendar_view(self):
        frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"])
        frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Header (Month Year + Nav)
        head = ctk.CTkFrame(frame, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(head, text="<", width=40, command=self.prev_month, fg_color=COLORS["bg_dark"]).pack(side="left")
        
        self.lbl_month = ctk.CTkLabel(head, text=f"{calendar.month_name[self.month]} {self.year}", 
                                      font=FONTS["h2"], text_color=COLORS["text_main"])
        self.lbl_month.pack(side="left", expand=True)
        
        ctk.CTkButton(head, text=">", width=40, command=self.next_month, fg_color=COLORS["bg_dark"]).pack(side="right")
        
        # Grid
        self.grid_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.render_calendar()
        
    def _create_event_sidebar(self):
        frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"])
        frame.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        
        ctk.CTkLabel(frame, text="AGENDA", font=FONTS["h3"], text_color=COLORS["accent"]).pack(anchor="w", padx=20, pady=20)
        
        # Mock Events
        events = [
            ("09:00 AM", "Daily Standup"),
            ("01:00 PM", "Deep Work Session"),
            ("05:00 PM", "Gym"),
            ("08:00 PM", "Review Code")
        ]
        
        for time, title in events:
            ef = ctk.CTkFrame(frame, fg_color=COLORS["bg_dark"], height=50)
            ef.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(ef, text=time, font=FONTS["tiny_bold"], text_color=COLORS["accent"]).pack(side="left", padx=10)
            ctk.CTkLabel(ef, text=title, font=FONTS["body"], text_color=COLORS["text_main"]).pack(side="left", padx=5)

    def render_calendar(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
            
        cal = calendar.monthcalendar(self.year, self.month)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        # Headers
        for i, d in enumerate(days):
            ctk.CTkLabel(self.grid_frame, text=d, font=FONTS["tiny_bold"], text_color=COLORS["text_dim"]).grid(row=0, column=i, pady=5)
            
        # Days
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day == 0: continue
                
                is_today = (day == datetime.now().day and self.month == datetime.now().month and self.year == datetime.now().year)
                color = COLORS["accent"] if is_today else COLORS["bg_dark"]
                text_color = COLORS["text_dark"] if is_today else COLORS["text_main"]
                
                btn = ctk.CTkButton(self.grid_frame, text=str(day), width=40, height=40, 
                                    fg_color=color, text_color=text_color, hover_color=COLORS["accent_hover"],
                                    command=lambda d=day: self.select_day(d))
                btn.grid(row=r+1, column=c, padx=5, pady=5)
                
    def prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self.lbl_month.configure(text=f"{calendar.month_name[self.month]} {self.year}")
        self.render_calendar()
        
    def next_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.lbl_month.configure(text=f"{calendar.month_name[self.month]} {self.year}")
        self.render_calendar()
        
    def select_day(self, day):
        print(f"Selected: {self.year}-{self.month}-{day}")
