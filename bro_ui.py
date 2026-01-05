"""
BRO Ultimate UI
Sci-fi inspired, fully offline desktop interface.
Features:
- 🎤 Real-time Voice Interaction
- 📈 Live System Graphs (Matplotlib)
- 📊 Advanced Dashboard
- 📱 Phone Control & Shopping
- 📅 Calendar & Notes
- 💎 Modern Dark Theme with Mini-Mode
"""

import os
import sys
import threading
import time
from datetime import datetime
from collections import deque

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from PIL import Image

# Theme Setup
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")  # Sleek blue accent

# Constants
HISTORY_LEN = 20  # Graph history points
REFRESH_RATE = 1000  # ms


class BROApp(ctk.CTk):
    """The Ultimate BRO Interface."""
    
    def __init__(self):
        super().__init__()
        
        # Window Config
        self.title("BRO AI - Ultimate Edition")
        self.geometry("1400x900")
        self.minsize(1000, 700)
        
        # Data for Graphs
        self.cpu_history = deque([0]*HISTORY_LEN, maxlen=HISTORY_LEN)
        self.ram_history = deque([0]*HISTORY_LEN, maxlen=HISTORY_LEN)
        
        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Setup UI
        self.create_sidebar()
        self.create_main_area()
        self.create_status_bar()
        
        # Start background tasks
        self.running = True
        self.after(100, self.update_system_stats)
        self.after(500, self.update_time)
        
        # Initialize Cognitive Brain (Background load)
        threading.Thread(target=self.init_brain, daemon=True).start()

    def init_brain(self):
        """Initialize the AI Brain in background."""
        try:
            self.after(0, lambda: self.add_message("BRO", "Initializing core systems...", save=False))
            from llm.cognitive_brain import CognitiveBrain
            self.brain = CognitiveBrain()
            self.brain.set_confirmation_callback(self.gui_confirmation)
            
            # Ready message
            self.after(0, lambda: self.add_message("BRO", "Systems online. How can I help? 🚀", save=False))
            print("✅ Cognitive Brain Attached")
        except Exception as e:
            print(f"❌ Brain Init Error: {e}")
            self.brain = None
            self.after(0, lambda: self.add_message("BRO", f"❌ Error initializing AI: {e}", save=False))
            
    def gui_confirmation(self, action_name, args):
        """GUI Popup for Tool Confirmation."""
        # We need to pause the thread waiting for this, so we use a variable
        resp = [None]
        
        def _ask():
            msg = f"⚠️ Allow Action?\n\nTool: {action_name}\nArgs: {args}"
            import tkinter.messagebox as mb
            do_it = mb.askyesno("BRO Security", msg, parent=self)
            resp[0] = do_it
            
        # Run on main thread
        self.after(0, _ask)
        
        # Wait for response (simple polling)
        while resp[0] is None:
            time.sleep(0.1)
            
        return resp[0]

    def create_sidebar(self):
        """Modern Gradient-like Sidebar."""
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=("#2b2b2b", "#1a1a1a"))
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)
        
        # Header - Clean & Bold
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=(40, 20), sticky="ew")
        
        ctk.CTkLabel(title_frame, text="BRO", font=("Segoe UI", 36, "bold"), text_color="#3B8ED0").pack(side="left")
        ctk.CTkLabel(title_frame, text="AI", font=("Segoe UI", 36, "bold"), text_color="white").pack(side="left", padx=5)
        
        ctk.CTkLabel(self.sidebar, text="SYSTEM ONLINE", font=("Segoe UI", 10, "bold"), text_color="#00ff00").grid(row=1, column=0, padx=20, pady=(0, 30), sticky="w")
        
        # Navigation with better spacing and hover
        self.nav_buttons = {}
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
                self.sidebar, 
                text=txt, 
                font=("Segoe UI", 14), 
                fg_color="transparent", 
                text_color=("gray10", "gray90"),
                hover_color=("#3B8ED0", "#1f538d"),
                anchor="w",
                height=50,
                corner_radius=8,
                command=lambda k=key: self.show_page(k)
            )
            btn.grid(row=i+2, column=0, padx=15, pady=4, sticky="ew")
            self.nav_buttons[key] = btn
            
        # Mini Mode
        mini_btn = ctk.CTkButton(self.sidebar, text="📱 Mini View", fg_color="#333", hover_color="#444", 
                                 font=("Segoe UI", 12), command=self.toggle_mini_mode)
        mini_btn.grid(row=11, column=0, padx=20, pady=20)

    def create_main_area(self):
        """Main Content Area - Clean Background."""
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color=("#f0f0f0", "#101010"))
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)
        
        self.pages = {}
        self.create_pages()
        self.show_page("chat")

    def create_pages(self):
        self.create_chat_page()
        self.create_dashboard_page()
        self.create_calendar_page()
        self.create_shopping_page()
        self.create_phone_page()
        self.create_notes_page()
        self.create_music_page()
        self.create_vision_page()
        self.create_web_page()
        self.create_settings_page()

    def create_chat_page(self):
        page = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.pages["chat"] = page
        
        # Chat Header
        header = ctk.CTkFrame(page, height=40, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(10, 0))
        
        ctk.CTkLabel(header, text="💬 Live Chat", font=("Segoe UI", 16, "bold"), text_color="gray").pack(side="left")
        ctk.CTkButton(header, text="🗑️ Clear", width=80, height=30, fg_color="#333", hover_color="#444",
                      command=self.clear_chat_ui).pack(side="right")

        # Chat History - SCROLLABLE FRAME (for Bubbles)
        self.chat_scroll = ctk.CTkScrollableFrame(page, fg_color="transparent")
        self.chat_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.add_message("BRO", "Systems initialized. Ready to assist. 🚀", save=False)
        self.load_chat_history()
        
        # Input Area - Floating Bar Look
        input_container = ctk.CTkFrame(page, fg_color=("white", "#1a1a1a"), height=70, corner_radius=20)
        input_container.pack(fill="x", padx=20, pady=(0, 20))
        
        self.mic_btn = ctk.CTkButton(input_container, text="🎤", width=45, height=45, 
                                     fg_color="#cc0000", hover_color="#ff3333", corner_radius=50,
                                     font=("Segoe UI", 18), command=self.start_listening)
        self.mic_btn.pack(side="left", padx=15, pady=10)
        
        self.chat_input = ctk.CTkEntry(input_container, placeholder_text="Type a message to BRO...", 
                                       height=45, font=("Segoe UI", 14), border_width=0, fg_color="transparent")
        self.chat_input.pack(side="left", fill="x", expand=True, padx=5)
        self.chat_input.bind("<Return>", lambda e: self.send_chat())
        
        send = ctk.CTkButton(input_container, text="➤", width=45, height=45, corner_radius=50, 
                             fg_color="#3B8ED0", hover_color="#1f538d", font=("Segoe UI", 18),
                             command=self.send_chat)
        send.pack(side="right", padx=15)

    def create_dashboard_page(self):
        page = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.pages["dashboard"] = page
        
        # Top Stats Row
        stats = ctk.CTkFrame(page, fg_color="transparent")
        stats.pack(fill="x", padx=20, pady=20)
        
        self.lbl_cpu = self._stat_card(stats, "CPU", "0%")
        self.lbl_ram = self._stat_card(stats, "RAM", "0%")
        self.lbl_gpu = self._stat_card(stats, "GPU", "N/A")
        self.lbl_bat = self._stat_card(stats, "PWR", "100%")
        
        # Graph Area (Canvas based - Lightweight)
        self.graph_frame = ctk.CTkFrame(page, fg_color="#1e1e1e", corner_radius=15)
        self.graph_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.graph_canvas = ctk.CTkCanvas(self.graph_frame, bg="#1e1e1e", highlightthickness=0)
        self.graph_canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initial draw
        self.after(100, self.update_graph_canvas)

    def update_system_stats(self):
        """Update data and redraw canvas (Optimized)."""
        try:
            from tools.system_monitor import get_cpu_usage, get_memory_usage
            c = get_cpu_usage()['usage']
            m = get_memory_usage()['percent']
            
            # Update cards
            self.lbl_cpu.configure(text=f"{c}%")
            self.lbl_ram.configure(text=f"{m}%")
            
            # Update Graph Data
            self.cpu_history.append(c)
            self.ram_history.append(m)
            
            self.update_graph_canvas()
            
        except Exception as e:
            print("Stat error:", e)
        
        self.after(2000, self.update_system_stats) # Slower refresh (2s)

    def update_graph_canvas(self):
        """Draw graph manually on canvas (Zero Lag)."""
        if not hasattr(self, 'graph_canvas'): return
        
        w = self.graph_canvas.winfo_width()
        h = self.graph_canvas.winfo_height()
        if w < 10 or h < 10: return
        
        self.graph_canvas.delete("all")
        
        # Draw grid lines
        for i in range(0, h, 40):
            self.graph_canvas.create_line(0, i, w, i, fill="#333", dash=(2, 4))
        
        # Plot CPU (Blue)
        if len(self.cpu_history) > 1:
            points = []
            step = w / (HISTORY_LEN - 1)
            for i, val in enumerate(self.cpu_history):
                x = i * step
                y = h - (val / 100 * h) # Scale 0-100 to height
                points.extend([x, y])
            self.graph_canvas.create_line(points, fill="#00aaff", width=2, smooth=True)
            
        # Plot RAM (Pink)
        if len(self.ram_history) > 1:
            points = []
            step = w / (HISTORY_LEN - 1)
            for i, val in enumerate(self.ram_history):
                x = i * step
                y = h - (val / 100 * h)
                points.extend([x, y])
            self.graph_canvas.create_line(points, fill="#ff00aa", width=2, smooth=True)

    def create_calendar_page(self):
        """Calendar Page."""
        page = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.pages["calendar"] = page
        
        head = ctk.CTkLabel(page, text="📅 MISSION TIMELINE", font=("Roboto", 24, "bold"))
        head.pack(pady=20)
        
        # Quick Add
        add_box = ctk.CTkFrame(page)
        add_box.pack(pady=10)
        self.cal_title = ctk.CTkEntry(add_box, placeholder_text="Event Title", width=200)
        self.cal_title.pack(side="left", padx=5)
        self.cal_time = ctk.CTkEntry(add_box, placeholder_text="Time (e.g. tomorrow 2pm)", width=150)
        self.cal_time.pack(side="left", padx=5)
        ctk.CTkButton(add_box, text="ADD", width=60, command=self.add_event_ui).pack(side="left", padx=5)
        
        # Calendar Text Area
        self.cal_text = ctk.CTkTextbox(page, font=("Consolas", 12))
        self.cal_text.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Refresh on load
        self.after(500, self.refresh_calendar)

    def create_shopping_page(self):
        page = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.pages["shopping"] = page
        ctk.CTkLabel(page, text="🛒 SUPPLY LOGISTICS", font=("Roboto", 24, "bold")).pack(pady=20)
        
        input_fr = ctk.CTkFrame(page)
        input_fr.pack(pady=10)
        self.shop_in = ctk.CTkEntry(input_fr, placeholder_text="Item...", width=250)
        self.shop_in.pack(side="left", padx=5)
        ctk.CTkButton(input_fr, text="ADD", width=80, command=self.add_shop_ui).pack(side="left", padx=5)
        
        self.shop_list = ctk.CTkTextbox(page, font=("Roboto", 14))
        self.shop_list.pack(fill="both", expand=True, padx=20, pady=10)
        self.after(500, self.refresh_shop)

    # ... (Other pages like Phone, Notes, Music, Settings would follow same pattern)
    # simplified for this upgrade focused on UI structure
    
    def create_phone_page(self):
        # reuse placeholder
        p = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.pages["phone"] = p
        ctk.CTkLabel(p, text="📱 DEVICE LINK", font=("Roboto", 24, "bold")).pack(pady=20)
        self.phone_status = ctk.CTkLabel(p, text="Scanning...", font=("Consolas", 14))
        self.phone_status.pack(pady=10)
        
        grid = ctk.CTkFrame(p)
        grid.pack(pady=20)
        ctk.CTkButton(grid, text="HOME", command=lambda: self.run_phone("home")).pack(side="left", padx=5)
        ctk.CTkButton(grid, text="BACK", command=lambda: self.run_phone("back")).pack(side="left", padx=5)
        ctk.CTkButton(grid, text="📸 SNAP", command=lambda: self.run_phone("snap")).pack(side="left", padx=5)

    def create_notes_page(self):
        p = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.pages["notes"] = p
        ctk.CTkLabel(p, text="📝 DATA LOGS", font=("Roboto", 24, "bold")).pack(pady=20)
        self.notes_txt = ctk.CTkTextbox(p)
        self.notes_txt.pack(fill="both", expand=True, padx=20, pady=20)
        self.after(500, self.refresh_notes)

    def create_music_page(self):
        p = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.pages["music"] = p
        ctk.CTkLabel(p, text="🎵 AUDIO SUBSYSTEM", font=("Roboto", 24, "bold")).pack(pady=20)
        ctrl = ctk.CTkFrame(p)
        ctrl.pack(pady=20)
        ctk.CTkButton(ctrl, text="⏮", width=50, command=lambda: self.run_music("prev")).pack(side="left", padx=5)
        ctk.CTkButton(ctrl, text="⏯", width=50, command=lambda: self.run_music("play")).pack(side="left", padx=5)
        ctk.CTkButton(ctrl, text="⏭", width=50, command=lambda: self.run_music("next")).pack(side="left", padx=5)

    def create_settings_page(self):
        p = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.pages["settings"] = p
        ctk.CTkLabel(p, text="⚙️ SYSTEM CONFIG", font=("Roboto", 24, "bold")).pack(pady=20)
        ctk.CTkLabel(p, text="BRO AI - v2.0 Ultimate").pack(pady=10)
        
        # System checks
        checks = ctk.CTkFrame(p)
        checks.pack(pady=20, padx=20, fill="x")
        
        from tools.vision import vision_status
        v_stat = vision_status()
        t = "✅ LLaVA Ready" if v_stat['llava_available'] else "❌ LLaVA (Vision) Missing"
        ctk.CTkLabel(checks, text=t).pack(anchor="w", padx=10, pady=5)
        
        try:
            from tools.web_automation import browser_status
            w_stat = browser_status()
            t = "✅ Playwright Ready" if w_stat['playwright_available'] else "❌ Playwright Missing"
        except: t = "❌ Web Module Error"
        ctk.CTkLabel(checks, text=t).pack(anchor="w", padx=10, pady=5)

    def create_vision_page(self):
        p = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.pages["vision"] = p
        
        ctk.CTkLabel(p, text="👁️ VISION SUBSYSTEM", font=("Roboto", 24, "bold")).pack(pady=20)
        
        # Control Bar
        ctrl = ctk.CTkFrame(p)
        ctrl.pack(pady=10)
        
        ctk.CTkButton(ctrl, text="📸 ANALYZE SCREEN", width=150, fg_color="#E04F5F", hover_color="#C03949",
                      command=lambda: self.run_vision("analyze")).pack(side="left", padx=10)
        
        ctk.CTkButton(ctrl, text="📝 READ TEXT (OCR)", width=150, fg_color="#3B8ED0", 
                      command=lambda: self.run_vision("ocr")).pack(side="left", padx=10)
        
        # Display Area
        self.vis_preview = ctk.CTkLabel(p, text="[No Image]", width=400, height=250, fg_color="#222", corner_radius=10)
        self.vis_preview.pack(pady=20)
        
        self.vis_result = ctk.CTkTextbox(p, font=("Consolas", 14), height=200)
        self.vis_result.pack(fill="x", padx=40, pady=10)
        
    def create_web_page(self):
        p = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.pages["web"] = p
        
        ctk.CTkLabel(p, text="🌐 WEB AUTOMATION", font=("Roboto", 24, "bold")).pack(pady=15)
        
        # Nav Bar
        nav = ctk.CTkFrame(p)
        nav.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(nav, text="⬅", width=40, command=lambda: self.run_web("back")).pack(side="left", padx=5)
        
        self.web_url = ctk.CTkEntry(nav, placeholder_text="https://...", height=35)
        self.web_url.pack(side="left", fill="x", expand=True, padx=5)
        self.web_url.bind("<Return>", lambda e: self.run_web("go"))
        
        ctk.CTkButton(nav, text="GO", width=60, command=lambda: self.run_web("go")).pack(side="left", padx=5)
        ctk.CTkButton(nav, text="📷 SNAP", width=80, fg_color="#555", command=lambda: self.run_web("snap")).pack(side="left", padx=5)
        
        # Status
        self.web_status = ctk.CTkLabel(p, text="Ready. Browser inactive.", font=("Segoe UI", 12), text_color="gray")
        self.web_status.pack(pady=5)
        
        # Quick Bookmarks
        bookmarks = ctk.CTkFrame(p)
        bookmarks.pack(pady=20)
        ctk.CTkLabel(bookmarks, text="Quick Links:").pack(side="left", padx=10)
        
        links = [("Google", "google.com"), ("YouTube", "youtube.com"), ("GitHub", "github.com"), ("News", "bbc.com")]
        for name, url in links:
            ctk.CTkButton(bookmarks, text=name, width=80, fg_color="transparent", border_width=1,
                          command=lambda u=url: self.run_web("go", u)).pack(side="left", padx=5)

    def run_vision(self, action):
        self.vis_result.delete("0.0", "end")
        self.vis_result.insert("0.0", "Processing... please wait...")
        self.update()
        
        def _t():
            try:
                from tools.vision import analyze_screen, read_screen_text, save_screenshot
                
                # Show preview first
                snap_path = save_screenshot()
                if "❌" not in snap_path:
                    path = snap_path.split(": ")[1].strip()
                    try:
                        # Load and show preview thumbnail
                        img = Image.open(path)
                        img.thumbnail((400, 250))
                        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                        self.after(0, lambda: self.vis_preview.configure(image=ctk_img, text=""))
                    except: pass
                
                result = ""
                if action == "analyze":
                    result = analyze_screen()
                elif action == "ocr":
                    result = read_screen_text()
                    
                self.after(0, lambda: self.vis_result.delete("0.0", "end"))
                self.after(0, lambda: self.vis_result.insert("0.0", result))
            except Exception as e:
                self.after(0, lambda: self.vis_result.insert("0.0", f"Error: {e}"))
                
        threading.Thread(target=_t).start()

    def run_web(self, action, override_url=None):
        def _t():
            from tools.web_automation import navigate_to, go_back, take_page_screenshot, get_current_url
            
            res = ""
            if action == "go":
                url = override_url if override_url else self.web_url.get()
                self.after(0, lambda: self.web_status.configure(text=f"Navigating to {url}..."))
                res = navigate_to(url)
            elif action == "back":
                res = go_back()
            elif action == "snap":
                res = take_page_screenshot()
                if "✓" in res:
                    os.system(f"start {res.split(': ')[1].strip()}") # Open image
            
            curr = get_current_url()
            self.after(0, lambda: self.web_status.configure(text=f"{curr} | Last: {res}"))
            
        threading.Thread(target=_t).start()

    # --- HELPERS ---

    def _stat_card(self, parent, title, val):
        f = ctk.CTkFrame(parent, fg_color="#2b2b2b", width=150, height=80)
        f.pack(side="left", padx=10, fill="y")
        ctk.CTkLabel(f, text=title, text_color="gray").pack(pady=(10,0))
        lbl = ctk.CTkLabel(f, text=val, font=("Roboto", 20, "bold"))
        lbl.pack(pady=(0,10))
        return lbl

    def create_status_bar(self):
        bar = ctk.CTkFrame(self, height=25, corner_radius=0, fg_color="#000")
        bar.grid(row=1, column=1, sticky="ew")
        self.lbl_time = ctk.CTkLabel(bar, text="--:--", text_color="#00aaff")
        self.lbl_time.pack(side="right", padx=15)
        ctk.CTkLabel(bar, text="Network: SECURE | AI: ONLINE", text_color="#555").pack(side="left", padx=15)

    # --- LOGIC ---

    def show_page(self, name):
        for n, p in self.pages.items():
            if n == name: p.pack(fill="both", expand=True)
            else: p.pack_forget()
        # Highlight nav
        for n, b in self.nav_buttons.items():
            b.configure(fg_color="#333" if n == name else "transparent")

    def toggle_mini_mode(self):
        # Simple toggle - resizing window
        w = self.winfo_width()
        if w > 500:
            self.geometry("400x600")
            self.sidebar.grid_remove() # Hide sidebar
            # Add a back button to main area? For now just manual resize back
        else:
            self.geometry("1400x900")
            self.sidebar.grid()

    def update_time(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.lbl_time.configure(text=now)
        self.after(1000, self.update_time)



    def send_chat(self):
        msg = self.chat_input.get().strip()
        if not msg: return
        self.chat_input.delete(0, "end")
        self.add_message("You", msg)
        
        threading.Thread(target=self._ai_reply, args=(msg,)).start()

    def _ai_reply(self, msg):
        if hasattr(self, 'brain') and self.brain:
            try:
                # Use Full Cognitive Brain
                self.after(0, lambda: self.web_status.configure(text="Thinking...") if hasattr(self, 'web_status') else None)
                resp = self.brain.process(msg)
            except Exception as e:
                resp = f"Brain Freeze 🥶: {e}"
        else:
            # Fallback
            from cognitive.personality import chat
            resp = chat(msg)
            
        self.after(0, lambda: self.add_message("BRO", resp))
        if hasattr(self, 'web_status'):
             self.after(0, lambda: self.web_status.configure(text="Ready"))

    # --- PERSISTENCE ---
    
    def load_chat_history(self):
        """Load chat history from file."""
        import json
        history_file = os.path.join(os.path.dirname(__file__), "bro_memory", "chat_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f:
                    data = json.load(f)
                    for msg in data:
                        self.add_message(msg["sender"], msg["text"], save=False)
            except Exception as e:
                print(f"Error loading history: {e}")

    def save_chat_message(self, sender, text):
        """Save a message to history."""
        import json
        history_file = os.path.join(os.path.dirname(__file__), "bro_memory", "chat_history.json")
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        
        # Load existing
        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f:
                    history = json.load(f)
            except: pass
        
        # Append new
        history.append({
            "sender": sender,
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep last 50
        history = history[-50:]
        
        # Save
        with open(history_file, "w") as f:
            json.dump(history, f)

    def clear_chat_ui(self):
        """Clear all chat messages."""
        # Visual Clear
        for widget in self.chat_scroll.winfo_children():
            widget.destroy()
            
        # File Clear
        history_file = os.path.join(os.path.dirname(__file__), "bro_memory", "chat_history.json")
        if os.path.exists(history_file):
            try:
                os.remove(history_file)
            except: pass
            
        # Reset
        self.add_message("BRO", "Chat cleared. Ready for new commands. 🧹", save=False)

    def add_message(self, sender, text, save=True):
        """Add a Chat Bubble."""
        if save:
            self.save_chat_message(sender, text)
            
        # Bubble Container
        bubble_frame = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        bubble_frame.pack(fill="x", pady=5)
        
        is_me = sender == "You"
        
        # Colors
        bg_color = "#3B8ED0" if is_me else "#333333"
        text_color = "white"
        
        # Bubble
        msg_frame = ctk.CTkFrame(bubble_frame, fg_color=bg_color, corner_radius=15)
        
        if is_me:
            msg_frame.pack(side="right", padx=(50, 0))
        else:
            msg_frame.pack(side="left", padx=(0, 50))
            
        # Text
        ctk.CTkLabel(msg_frame, text=text, font=("Segoe UI", 13), text_color=text_color, 
                     wraplength=400, justify="left").pack(padx=15, pady=10)
        
        # Tiny Timestamp
        timestamp = datetime.now().strftime("%I:%M %p")
        time_lbl = ctk.CTkLabel(bubble_frame, text=timestamp, font=("Segoe UI", 9), text_color="gray")
        
        if is_me:
            time_lbl.pack(side="right", padx=5, anchor="s")
        else:
            time_lbl.pack(side="left", padx=5, anchor="s")
            
        # Scroll to bottom
        self.update_idletasks()
        self.chat_scroll._parent_canvas.yview_moveto(1.0)

    def start_listening(self):
        """Real Voice Listening."""
        if hasattr(self, "recording") and self.recording:
            return

        self.recording = True
        self.mic_btn.configure(fg_color="#00ff00") # Green
        self.chat_input.delete(0, "end")
        self.chat_input.insert(0, "Listening... (Speak now)")
        self.update() 
        
        def _listen_thread():
            try:
                from tools.voice_input import listen_and_transcribe
                text, error = listen_and_transcribe()
                
                self.after(0, lambda: self._finish_listening(text, error))
            except Exception as e:
                print(f"Voice Error: {e}")
                self.after(0, lambda: self._finish_listening(None, str(e)))
        
        threading.Thread(target=_listen_thread).start()

    def _finish_listening(self, text, error):
        self.recording = False
        self.mic_btn.configure(fg_color="#cc0000")
        self.chat_input.delete(0, "end")
        
        if error:
            self.chat_input.insert(0, f"Error: {error}")
        elif text:
            self.chat_input.insert(0, text)
            self.send_chat()
        else:
            self.chat_input.placeholder_text = "No speech detected"

    # ... UI Wiring actions ... 
    def refresh_calendar(self):
        from tools.calendar import upcoming
        self.cal_text.delete("0.0", "end")
        self.cal_text.insert("0.0", upcoming(7))
        
    def add_event_ui(self):
        t = self.cal_title.get()
        w = self.cal_time.get()
        if t and w: 
            from tools.calendar import add_event
            add_event(t, w)
            self.refresh_calendar()
            self.cal_title.delete(0, "end")
            self.cal_time.delete(0, "end")

    def refresh_shop(self):
        from tools.smart_shopping import get_list
        self.shop_list.delete("0.0", "end")
        self.shop_list.insert("0.0", get_list())

    def add_shop_ui(self):
        i = self.shop_in.get()
        if i:
            from tools.smart_shopping import shop_from_text
            shop_from_text(i)
            self.shop_in.delete(0, "end")
            self.refresh_shop()

    def run_phone(self, cmd):
        def _t():
            from tools.android_control import AndroidController
            ctrl = AndroidController()
            if ctrl.connect():
                if cmd == "home": ctrl.press_key("home")
                elif cmd == "back": ctrl.press_key("back")
                elif cmd == "snap": ctrl.capture_screen()
                self.phone_status.configure(text=f"Action '{cmd}' Done")
            else:
                self.phone_status.configure(text="Connect failed.")
        threading.Thread(target=_t).start()
        
    def refresh_notes(self):
        from tools.reminders import notes
        self.notes_txt.delete("0.0", "end")
        self.notes_txt.insert("0.0", notes())

    def run_music(self, cmd):
        from tools.music_player import play_pause, next_track, previous_track
        if cmd == "play": play_pause()
        elif cmd == "next": next_track()
        elif cmd == "prev": previous_track()

if __name__ == "__main__":
    app = BROApp()
    app.mainloop()
