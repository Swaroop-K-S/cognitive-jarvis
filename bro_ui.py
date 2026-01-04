"""
BRO Desktop UI
Modern desktop interface for BRO AI Assistant.
Built with CustomTkinter for a sleek, modern look.
"""

import os
import sys
import threading
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from PIL import Image

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class BROApp(ctk.CTk):
    """Main BRO Application Window."""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("BRO - Your AI Best Friend")
        self.geometry("1200x800")
        self.minsize(900, 600)
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create sidebar
        self.create_sidebar()
        
        # Create main content area
        self.create_main_area()
        
        # Create status bar
        self.create_status_bar()
        
        # Load initial data
        self.after(100, self.load_initial_data)
    
    def create_sidebar(self):
        """Create the sidebar with navigation."""
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        sidebar.grid_rowconfigure(10, weight=1)
        
        # Logo/Title
        logo_label = ctk.CTkLabel(
            sidebar, 
            text="🤖 BRO",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 5))
        
        subtitle = ctk.CTkLabel(
            sidebar,
            text="Your AI Best Friend",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("💬 Chat", "chat"),
            ("📊 Dashboard", "dashboard"),
            ("🛒 Shopping", "shopping"),
            ("📱 Phone", "phone"),
            ("📝 Notes", "notes"),
            ("🎵 Music", "music"),
            ("⚙️ Settings", "settings"),
        ]
        
        for i, (text, key) in enumerate(nav_items):
            btn = ctk.CTkButton(
                sidebar,
                text=text,
                font=ctk.CTkFont(size=14),
                height=40,
                anchor="w",
                command=lambda k=key: self.show_page(k)
            )
            btn.grid(row=i+2, column=0, padx=10, pady=5, sticky="ew")
            self.nav_buttons[key] = btn
        
        # Spacer
        spacer = ctk.CTkLabel(sidebar, text="")
        spacer.grid(row=10, column=0, sticky="nsew")
        
        # System status at bottom
        self.system_label = ctk.CTkLabel(
            sidebar,
            text="💻 Loading...",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.system_label.grid(row=11, column=0, padx=20, pady=10)
    
    def create_main_area(self):
        """Create the main content area."""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Container for pages
        self.pages = {}
        
        # Create all pages
        self.create_chat_page()
        self.create_dashboard_page()
        self.create_shopping_page()
        self.create_phone_page()
        self.create_notes_page()
        self.create_music_page()
        self.create_settings_page()
        
        # Show default page
        self.show_page("chat")
    
    def create_chat_page(self):
        """Create the chat page."""
        page = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.pages["chat"] = page
        
        # Chat header
        header = ctk.CTkLabel(
            page, 
            text="💬 Chat with BRO",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=(0, 20))
        
        # Chat history
        self.chat_history = ctk.CTkTextbox(
            page, 
            height=400,
            font=ctk.CTkFont(size=13),
            state="disabled"
        )
        self.chat_history.pack(fill="both", expand=True, pady=(0, 10))
        
        # Add welcome message
        self.add_chat_message("BRO", "Hey! I'm BRO, your AI best friend. What's up? 😊")
        
        # Input frame
        input_frame = ctk.CTkFrame(page, fg_color="transparent")
        input_frame.pack(fill="x", pady=(0, 10))
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.chat_input = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your message...",
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.chat_input.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.chat_input.bind("<Return>", lambda e: self.send_message())
        
        send_btn = ctk.CTkButton(
            input_frame,
            text="Send",
            width=100,
            height=45,
            command=self.send_message
        )
        send_btn.grid(row=0, column=1)
        
        # Quick actions
        quick_frame = ctk.CTkFrame(page, fg_color="transparent")
        quick_frame.pack(fill="x")
        
        quick_actions = [
            ("🌤️ Weather", "What's the weather?"),
            ("💻 System", "How's my system?"),
            ("📝 Notes", "Show my notes"),
            ("⏰ Reminders", "What are my reminders?"),
        ]
        
        for text, msg in quick_actions:
            btn = ctk.CTkButton(
                quick_frame,
                text=text,
                width=100,
                height=30,
                command=lambda m=msg: self.quick_message(m)
            )
            btn.pack(side="left", padx=5)
    
    def create_dashboard_page(self):
        """Create the dashboard page."""
        page = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.pages["dashboard"] = page
        
        header = ctk.CTkLabel(
            page,
            text="📊 Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=(0, 20))
        
        # Stats grid
        stats_frame = ctk.CTkFrame(page)
        stats_frame.pack(fill="x", pady=10)
        
        # Row 1
        row1 = ctk.CTkFrame(stats_frame, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=10)
        
        self.cpu_card = self.create_stat_card(row1, "🔲 CPU", "0%")
        self.ram_card = self.create_stat_card(row1, "🧠 RAM", "0%")
        self.battery_card = self.create_stat_card(row1, "🔋 Battery", "0%")
        self.gpu_card = self.create_stat_card(row1, "🎮 GPU", "0%")
        
        # Weather card
        weather_frame = ctk.CTkFrame(page)
        weather_frame.pack(fill="x", pady=10, padx=0)
        
        self.weather_label = ctk.CTkLabel(
            weather_frame,
            text="🌤️ Loading weather...",
            font=ctk.CTkFont(size=16)
        )
        self.weather_label.pack(pady=20)
        
        # Phone status
        phone_frame = ctk.CTkFrame(page)
        phone_frame.pack(fill="x", pady=10)
        
        self.phone_label = ctk.CTkLabel(
            phone_frame,
            text="📱 Checking phone connection...",
            font=ctk.CTkFont(size=14)
        )
        self.phone_label.pack(pady=20)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            page,
            text="🔄 Refresh",
            command=self.refresh_dashboard
        )
        refresh_btn.pack(pady=20)
    
    def create_stat_card(self, parent, title, value):
        """Create a stat card."""
        card = ctk.CTkFrame(parent)
        card.pack(side="left", expand=True, fill="both", padx=5)
        
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        title_label.pack(pady=(15, 5))
        
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        value_label.pack(pady=(0, 15))
        
        return value_label
    
    def create_shopping_page(self):
        """Create the shopping page."""
        page = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.pages["shopping"] = page
        
        header = ctk.CTkLabel(
            page,
            text="🛒 Smart Shopping",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=(0, 20))
        
        # Add item
        add_frame = ctk.CTkFrame(page, fg_color="transparent")
        add_frame.pack(fill="x", pady=10)
        
        self.shopping_input = ctk.CTkEntry(
            add_frame,
            placeholder_text="Add items (e.g., Milk, Bread, Eggs)",
            height=40
        )
        self.shopping_input.pack(side="left", expand=True, fill="x", padx=(0, 10))
        
        add_btn = ctk.CTkButton(
            add_frame,
            text="Add",
            width=80,
            command=self.add_shopping_item
        )
        add_btn.pack(side="right")
        
        # Shopping list
        self.shopping_list = ctk.CTkTextbox(page, height=300)
        self.shopping_list.pack(fill="both", expand=True, pady=10)
        
        # Action buttons
        action_frame = ctk.CTkFrame(page, fg_color="transparent")
        action_frame.pack(fill="x")
        
        ctk.CTkButton(action_frame, text="🔄 Refresh", command=self.refresh_shopping).pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text="🗑️ Clear", command=self.clear_shopping).pack(side="left", padx=5)
    
    def create_phone_page(self):
        """Create the phone control page."""
        page = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.pages["phone"] = page
        
        header = ctk.CTkLabel(
            page,
            text="📱 Phone Control",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=(0, 20))
        
        self.phone_status_label = ctk.CTkLabel(
            page,
            text="Checking connection...",
            font=ctk.CTkFont(size=14)
        )
        self.phone_status_label.pack(pady=10)
        
        # Control buttons
        controls = ctk.CTkFrame(page)
        controls.pack(pady=20)
        
        btns = [
            ("📸 Screenshot", self.phone_screenshot),
            ("🏠 Home", lambda: self.phone_key("home")),
            ("◀️ Back", lambda: self.phone_key("back")),
        ]
        
        for text, cmd in btns:
            ctk.CTkButton(controls, text=text, width=120, command=cmd).pack(side="left", padx=5)
    
    def create_notes_page(self):
        """Create the notes page."""
        page = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.pages["notes"] = page
        
        header = ctk.CTkLabel(
            page,
            text="📝 Notes & Reminders",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=(0, 20))
        
        # Add note
        add_frame = ctk.CTkFrame(page, fg_color="transparent")
        add_frame.pack(fill="x", pady=10)
        
        self.note_input = ctk.CTkEntry(
            add_frame,
            placeholder_text="Add a quick note...",
            height=40
        )
        self.note_input.pack(side="left", expand=True, fill="x", padx=(0, 10))
        
        ctk.CTkButton(add_frame, text="Add", width=80, command=self.add_note).pack(side="right")
        
        # Notes list
        self.notes_display = ctk.CTkTextbox(page, height=200)
        self.notes_display.pack(fill="both", expand=True, pady=10)
        
        # Reminders
        ctk.CTkLabel(page, text="⏰ Reminders", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))
        
        self.reminders_display = ctk.CTkTextbox(page, height=150)
        self.reminders_display.pack(fill="both", expand=True)
    
    def create_music_page(self):
        """Create the music control page."""
        page = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.pages["music"] = page
        
        header = ctk.CTkLabel(
            page,
            text="🎵 Music Control",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=(0, 30))
        
        # Playback controls
        controls = ctk.CTkFrame(page)
        controls.pack(pady=20)
        
        ctk.CTkButton(controls, text="⏮️", width=60, command=self.music_prev).pack(side="left", padx=5)
        ctk.CTkButton(controls, text="⏯️", width=80, command=self.music_play).pack(side="left", padx=5)
        ctk.CTkButton(controls, text="⏭️", width=60, command=self.music_next).pack(side="left", padx=5)
        
        # Volume
        vol_frame = ctk.CTkFrame(page, fg_color="transparent")
        vol_frame.pack(pady=20)
        
        ctk.CTkLabel(vol_frame, text="🔊 Volume").pack(side="left", padx=10)
        ctk.CTkButton(vol_frame, text="-", width=40, command=self.vol_down).pack(side="left")
        self.vol_label = ctk.CTkLabel(vol_frame, text="50%", width=60)
        self.vol_label.pack(side="left")
        ctk.CTkButton(vol_frame, text="+", width=40, command=self.vol_up).pack(side="left")
        ctk.CTkButton(vol_frame, text="🔇", width=40, command=self.vol_mute).pack(side="left", padx=10)
    
    def create_settings_page(self):
        """Create settings page."""
        page = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.pages["settings"] = page
        
        header = ctk.CTkLabel(
            page,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=(0, 20))
        
        # Appearance
        ctk.CTkLabel(page, text="Appearance", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(20, 10))
        
        theme_frame = ctk.CTkFrame(page, fg_color="transparent")
        theme_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(theme_frame, text="Theme:").pack(side="left")
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Dark", "Light", "System"],
            command=self.change_theme
        )
        theme_menu.pack(side="left", padx=10)
        
        # About
        about = ctk.CTkLabel(
            page,
            text="\n🤖 BRO AI Assistant\nVersion 1.0\n\n100% Offline • Local AI • Your Best Friend",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        about.pack(pady=40)
    
    def create_status_bar(self):
        """Create status bar at bottom."""
        status = ctk.CTkFrame(self, height=30, corner_radius=0)
        status.grid(row=1, column=1, sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            status,
            text="🤖 BRO Ready | 🟢 Ollama Connected",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(side="left", padx=10)
        
        self.time_label = ctk.CTkLabel(
            status,
            text="",
            font=ctk.CTkFont(size=11)
        )
        self.time_label.pack(side="right", padx=10)
        
        # Update time
        self.update_time()
    
    def update_time(self):
        """Update the time display."""
        now = datetime.now().strftime("%I:%M %p")
        self.time_label.configure(text=now)
        self.after(1000, self.update_time)
    
    def show_page(self, page_name):
        """Show a specific page."""
        for name, page in self.pages.items():
            if name == page_name:
                page.pack(fill="both", expand=True)
            else:
                page.pack_forget()
        
        # Update button states
        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color=("gray70", "gray30"))
    
    def load_initial_data(self):
        """Load initial data in background."""
        threading.Thread(target=self._load_data, daemon=True).start()
    
    def _load_data(self):
        """Background data loading."""
        try:
            # System info
            from tools.system_monitor import get_cpu_usage, get_memory_usage, get_battery_status, get_gpu_info
            
            cpu = get_cpu_usage()
            mem = get_memory_usage()
            bat = get_battery_status()
            gpu = get_gpu_info()
            
            self.after(0, lambda: self.cpu_card.configure(text=f"{cpu['usage']}%"))
            self.after(0, lambda: self.ram_card.configure(text=f"{mem['percent']}%"))
            self.after(0, lambda: self.battery_card.configure(text=f"{bat['percent'] or 'N/A'}%"))
            self.after(0, lambda: self.gpu_card.configure(text=f"{gpu.get('utilization', 'N/A')}%"))
            
            # Weather
            from tools.weather import quick_weather
            wx = quick_weather("Bangalore")
            self.after(0, lambda: self.weather_label.configure(text=wx))
            
            # Phone
            from tools.android_control import AndroidController
            ctrl = AndroidController()
            if ctrl.connect():
                self.after(0, lambda: self.phone_label.configure(text=f"📱 Connected: {ctrl.device.serial}"))
            else:
                self.after(0, lambda: self.phone_label.configure(text="📱 Not connected"))
            
            # System status
            self.after(0, lambda: self.system_label.configure(text=f"💻 CPU {cpu['usage']}% | RAM {mem['percent']}%"))
            
            # Notes
            from tools.reminders import notes, reminders
            self.after(0, lambda: self.notes_display.delete("0.0", "end"))
            self.after(0, lambda: self.notes_display.insert("0.0", notes()))
            self.after(0, lambda: self.reminders_display.delete("0.0", "end"))
            self.after(0, lambda: self.reminders_display.insert("0.0", reminders()))
            
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def add_chat_message(self, sender, message):
        """Add a message to chat history."""
        self.chat_history.configure(state="normal")
        timestamp = datetime.now().strftime("%I:%M %p")
        
        if sender == "You":
            self.chat_history.insert("end", f"\n[{timestamp}] You: {message}\n")
        else:
            self.chat_history.insert("end", f"\n[{timestamp}] 🤖 BRO: {message}\n")
        
        self.chat_history.configure(state="disabled")
        self.chat_history.see("end")
    
    def send_message(self):
        """Send a chat message."""
        msg = self.chat_input.get().strip()
        if not msg:
            return
        
        self.chat_input.delete(0, "end")
        self.add_chat_message("You", msg)
        
        # Get response in background
        threading.Thread(target=self._get_response, args=(msg,), daemon=True).start()
    
    def _get_response(self, message):
        """Get AI response in background."""
        try:
            from cognitive.personality import chat
            response = chat(message)
            self.after(0, lambda: self.add_chat_message("BRO", response))
        except Exception as e:
            self.after(0, lambda: self.add_chat_message("BRO", f"Error: {e}"))
    
    def quick_message(self, msg):
        """Send a quick action message."""
        self.chat_input.delete(0, "end")
        self.chat_input.insert(0, msg)
        self.send_message()
    
    def refresh_dashboard(self):
        """Refresh dashboard data."""
        threading.Thread(target=self._load_data, daemon=True).start()
    
    def add_shopping_item(self):
        """Add item to shopping list."""
        items = self.shopping_input.get().strip()
        if items:
            from tools.smart_shopping import shop_from_text
            shop_from_text(items)
            self.shopping_input.delete(0, "end")
            self.refresh_shopping()
    
    def refresh_shopping(self):
        """Refresh shopping list."""
        try:
            from tools.smart_shopping import get_list
            self.shopping_list.delete("0.0", "end")
            self.shopping_list.insert("0.0", get_list())
        except Exception as e:
            self.shopping_list.insert("0.0", f"Error: {e}")
    
    def clear_shopping(self):
        """Clear shopping list."""
        from tools.smart_shopping import clear_list
        clear_list()
        self.refresh_shopping()
    
    def phone_screenshot(self):
        """Take phone screenshot."""
        try:
            from tools.android_control import AndroidController
            ctrl = AndroidController()
            if ctrl.connect():
                path = ctrl.capture_screen()
                self.phone_status_label.configure(text=f"📸 Saved: {path}")
        except Exception as e:
            self.phone_status_label.configure(text=f"Error: {e}")
    
    def phone_key(self, key):
        """Send key to phone."""
        try:
            from tools.android_control import AndroidController
            ctrl = AndroidController()
            if ctrl.connect():
                ctrl.press_key(key)
                self.phone_status_label.configure(text=f"✅ Pressed {key}")
        except Exception as e:
            self.phone_status_label.configure(text=f"Error: {e}")
    
    def add_note(self):
        """Add a new note."""
        content = self.note_input.get().strip()
        if content:
            from tools.reminders import note
            note(content)
            self.note_input.delete(0, "end")
            self._load_data()
    
    def music_play(self):
        from tools.music_player import play_pause
        play_pause()
    
    def music_next(self):
        from tools.music_player import next_track
        next_track()
    
    def music_prev(self):
        from tools.music_player import previous_track
        previous_track()
    
    def vol_up(self):
        from tools.music_player import volume_up
        volume_up(10)
    
    def vol_down(self):
        from tools.music_player import volume_down
        volume_down(10)
    
    def vol_mute(self):
        from tools.music_player import mute
        mute()
    
    def change_theme(self, choice):
        """Change app theme."""
        ctk.set_appearance_mode(choice.lower())


def main():
    """Run the BRO app."""
    app = BROApp()
    app.mainloop()


if __name__ == "__main__":
    main()
