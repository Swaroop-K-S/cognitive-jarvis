import customtkinter as ctk
from jarvis.ui.theme import COLORS, FONTS

class ShoppingPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._create_header()
        self._create_grid()
        self.load_mock_data()
        
    def _create_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(head, text="🛒 SMART SHOPPING", font=FONTS["h2"], text_color=COLORS["text_dim"]).pack(side="left")
        
        ctk.CTkButton(head, text="+ Track Item", fg_color=COLORS["accent"], 
                      command=self.add_item).pack(side="right")
        
    def _create_grid(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 20))
        
        # Grid config for cards
        self.scroll.grid_columnconfigure(0, weight=1)
        self.scroll.grid_columnconfigure(1, weight=1)
        self.scroll.grid_columnconfigure(2, weight=1)
        
    def load_mock_data(self):
        items = [
            ("RTX 5090", "$1,599", "📉 Low Pice", "High Demand"),
            ("Mechanical Keyboard", "$120", "✅ In Stock", "Keychron Q1"),
            ("OLED Monitor 4K", "$899", "⚠️ Price Up", "LG C3"),
            ("Ergo Chair", "$450", "✅ In Stock", "Herman Miller"),
            ("DDR5 RAM 64GB", "$220", "📉 Low Price", "Corsair"),
            ("NVMe SSD 4TB", "$300", "✅ Stable", "Samsung 990 Pro"),
        ]
        
        for i, (name, price, status, note) in enumerate(items):
            row = i // 3
            col = i % 3
            self._create_card(row, col, name, price, status, note)
            
    def _create_card(self, row, col, name, price, status, note):
        card = ctk.CTkFrame(self.scroll, fg_color=COLORS["bg_card"], corner_radius=15)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Image placeholder
        img_box = ctk.CTkFrame(card, height=120, fg_color=COLORS["bg_dark"], corner_radius=15)
        img_box.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(img_box, text="📷", font=("Segoe UI", 30)).place(relx=0.5, rely=0.5, anchor="center")
        
        # Info
        ctk.CTkLabel(card, text=name, font=FONTS["body_bold"], text_color=COLORS["text_main"]).pack(anchor="w", padx=15)
        ctk.CTkLabel(card, text=price, font=FONTS["h3"], text_color=COLORS["accent"]).pack(anchor="w", padx=15)
        
        # Status Badge
        s_color = COLORS["text_success"] if "Low" in status or "In" in status else COLORS["text_error"]
        ctk.CTkLabel(card, text=status, font=FONTS["tiny_bold"], text_color=s_color).pack(anchor="w", padx=15, pady=5)
        
        # Actions
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(btns, text="Buy", height=25, width=60, fg_color=COLORS["accent"]).pack(side="right")
        ctk.CTkButton(btns, text="Check", height=25, width=60, fg_color=COLORS["bg_dark"]).pack(side="right", padx=5)

    def add_item(self):
        print("Add item dialog")
