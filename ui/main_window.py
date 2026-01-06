import customtkinter as ctk
import sys
import os

# Ensure project root is in path (3 levels up: ui/main_window.py -> ui -> jarvis -> root)


from jarvis.ui.theme import COLORS, apply_theme
from jarvis.ui.components.sidebar import Sidebar
from jarvis.ui.pages.chat_page import ChatPage
from jarvis.ui.pages.dashboard_page import DashboardPage
from jarvis.ui.pages.vision_page import VisionPage
from jarvis.ui.pages.web_page import WebPage
from jarvis.llm.cognitive_brain import CognitiveBrain
import threading

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Setup
        apply_theme(self)
        self.title("BRO AI - GLASS HUD")
        self.geometry("1280x800")
        
        # Initialize Brain (Lazy load or threading recommended for speed, but init here for now)
        self.brain = CognitiveBrain()
        
        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar = Sidebar(self, self.navigate, current_page="chat")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Main Area
        self.main_area = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        
        # Pages
        self.pages = {}
        self.current_page = None
        
        # Init Pages
        self._init_pages()
        self.navigate("chat")
        
    def _init_pages(self):
        self.pages["chat"] = ChatPage(self.main_area, self.handle_chat_message)
        self.pages["dashboard"] = DashboardPage(self.main_area)
        self.pages["vision"] = VisionPage(self.main_area)
        self.pages["web"] = WebPage(self.main_area)
        
    def navigate(self, page_name):
        if page_name == "mini_mode":
            print("To Mini Mode") # Todo
            return
            
        # Hide current
        if self.current_page:
            self.current_page.pack_forget()
            
        # Show new
        if page_name in self.pages:
            self.pages[page_name].pack(fill="both", expand=True)
            self.current_page = self.pages[page_name]
            self.sidebar.current_page = page_name
            self.sidebar.highlight_nav(page_name)
            
    def handle_chat_message(self, text):
        # Run processing in a thread to keep UI responsive
        threading.Thread(target=self._process_message_thread, args=(text,), daemon=True).start()
        
    def _process_message_thread(self, text):
        response = self.brain.process(text)
        # Schedule UI update on main thread
        self.after(0, lambda: self.pages["chat"].add_message("BRO", response, animate=True))

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
