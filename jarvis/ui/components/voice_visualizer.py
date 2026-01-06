import customtkinter as ctk
import random
import math
from jarvis.ui.theme import COLORS

class VoiceVisualizer(ctk.CTkCanvas):
    def __init__(self, parent, width=300, height=60, **kwargs):
        super().__init__(parent, width=width, height=height, bg=COLORS["bg_card"], highlightthickness=0, **kwargs)
        
        self.active = False
        self.bars = 30
        self.values = [10] * self.bars
        self.width_val = width
        self.height_val = height
        self.data_source = None
        
        self.after(50, self._animate)
        
    def set_active(self, active: bool):
        self.active = active
        
    def attach_stream(self, stream_analyzer):
        self.data_source = stream_analyzer

    def _animate(self):
        if not self.winfo_exists(): return
        
        self.delete("all")
        
        # Bar properties
        bar_w = (self.width_val / self.bars) - 2
        center_y = self.height_val / 2
        
        # Get Real Data
        target_levels = [5] * self.bars
        if self.active and self.data_source:
            try:
                target_levels = self.data_source.get_levels()
                # Ensure length match
                if len(target_levels) != self.bars:
                    target_levels = [5] * self.bars 
            except:
                pass
        
        for i in range(self.bars):
            # Target height
            if self.active and self.data_source:
                h = max(5, target_levels[i])
            elif self.active:
                # Fallback noise
                 t = (i / self.bars) * math.pi * 2
                 noise = random.randint(5, 25)
                 h = 10 + (math.sin(t + getattr(self, '_tick', 0)) * 10) + noise
            else:
                # Idle ripple
                h = 5 + random.randint(0, 3)
            
            # Smoothing
            self.values[i] = (self.values[i] * 0.5) + (h * 0.5)
            current_h = self.values[i]
            
            x = i * (bar_w + 2) + 2
            
            # Gradient Color based on active state
            color = "#00ffaa"  if self.active else "#333333" 
            if self.active and current_h > 30: color = "#ccff00" # Peak color
            
            self.create_rectangle(x, center_y - current_h, x + bar_w, center_y + current_h, fill=color, outline="")
            
        self._tick = getattr(self, '_tick', 0) + 0.5
        self.after(30, self._animate)
