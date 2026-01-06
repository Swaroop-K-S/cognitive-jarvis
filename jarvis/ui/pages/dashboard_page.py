import customtkinter as ctk
import time
from collections import deque
from jarvis.ui.theme import COLORS, FONTS

# Constants
HISTORY_LEN = 40  # More points for smoother graph
REFRESH_RATE = 1000  # ms

class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Data
        self.cpu_history = deque([0]*HISTORY_LEN, maxlen=HISTORY_LEN)
        self.ram_history = deque([0]*HISTORY_LEN, maxlen=HISTORY_LEN)
        self.running = True
        
        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1) # Graph expands
        
        self._create_header()
        self._create_stats_row()
        self._create_graph_area()
        
        # Start monitoring
        self.update_stats()
        
    def _create_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=20)
        ctk.CTkLabel(head, text="📈 SYSTEM DIAGNOSTICS", font=FONTS["h2"], text_color=COLORS["text_dim"]).pack(side="left")
        
    def _create_stats_row(self):
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
        
        self.lbl_cpu = self._stat_card(stats_frame, "CPU LOAD", "0%", COLORS["accent"])
        self.lbl_ram = self._stat_card(stats_frame, "RAM USAGE", "0%", COLORS["text_error"])  # Pinkish
        self.lbl_disk = self._stat_card(stats_frame, "DISK", "0%", COLORS["text_main"])
        
    def _stat_card(self, parent, title, val, color):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=15, width=160, height=100)
        card.pack(side="left", padx=10, expand=True, fill="x")
        
        ctk.CTkLabel(card, text=title, font=FONTS["tiny"], text_color=COLORS["text_dim"]).pack(pady=(15, 0))
        lbl = ctk.CTkLabel(card, text=val, font=("Roboto", 32, "bold"), text_color=color)
        lbl.pack(pady=(5, 15))
        return lbl

    def _create_graph_area(self):
        # Canvas Container
        self.graph_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=15)
        self.graph_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)
        
        self.graph_canvas = ctk.CTkCanvas(self.graph_frame, bg=COLORS["bg_card"], highlightthickness=0)
        self.graph_canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bind resize
        self.graph_canvas.bind("<Configure>", lambda e: self.draw_graph())

    def update_stats(self):
        if not self.winfo_exists():
            self.running = False
            return

        try:
            import psutil
            c = psutil.cpu_percent()
            m = psutil.virtual_memory().percent
            d = psutil.disk_usage('/').percent
            
            # Update labels
            self.lbl_cpu.configure(text=f"{c}%")
            self.lbl_ram.configure(text=f"{m}%")
            self.lbl_disk.configure(text=f"{d}%")
            
            # Update history
            self.cpu_history.append(c)
            self.ram_history.append(m)
            
            # Draw
            self.draw_graph()
            
        except Exception as e:
            print(f"Stat Error: {e}")
            
        if self.running:
            self.after(2000, self.update_stats)

    def draw_graph(self):
        w = self.graph_canvas.winfo_width()
        h = self.graph_canvas.winfo_height()
        if w < 10 or h < 10: return
        
        self.graph_canvas.delete("all")
        
        # Grid
        for i in range(0, h, 40):
            self.graph_canvas.create_line(0, i, w, i, fill="#444", dash=(2, 4), width=1)
            
        # Helper to plot
        def plot(data, color):
            if len(data) < 2: return
            points = []
            step = w / (HISTORY_LEN - 1)
            for i, val in enumerate(data):
                x = i * step
                y = h - (val / 100 * h)
                points.extend([x, y])
            self.graph_canvas.create_line(points, fill=color, width=3, smooth=True, capstyle="round")

        plot(self.cpu_history, COLORS["accent"])      # Blue
        plot(self.ram_history, COLORS["text_error"])  # Red/Pink
        
        # Legend
        self.graph_canvas.create_text(w-50, 20, text="CPU", fill=COLORS["accent"], font=("Roboto", 10), anchor="e")
        self.graph_canvas.create_text(w-50, 40, text="RAM", fill=COLORS["text_error"], font=("Roboto", 10), anchor="e")
