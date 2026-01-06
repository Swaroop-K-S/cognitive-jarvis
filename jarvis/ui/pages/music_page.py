import customtkinter as ctk
import os
import threading
from jarvis.ui.theme import COLORS, FONTS

class MusicPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.music_dir = os.path.join(os.path.expanduser("~"), "Music")
        self.current_track = None
        self.playing = False
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._create_player_controls()
        self._create_playlist()
        
    def _create_player_controls(self):
        # Top Player Area
        player = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=200, corner_radius=20)
        player.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        # Album Art Placeholder
        art = ctk.CTkFrame(player, width=150, height=150, fg_color=COLORS["bg_dark"])
        art.pack(side="left", padx=20, pady=20)
        ctk.CTkLabel(art, text="🎵", font=("Segoe UI", 40)).place(relx=0.5, rely=0.5, anchor="center")
        
        # Info & Controls
        info = ctk.CTkFrame(player, fg_color="transparent")
        info.pack(side="left", expand=True, fill="both", pady=20)
        
        self.lbl_track = ctk.CTkLabel(info, text="No Track Selected", font=FONTS["h2"], text_color=COLORS["text_main"])
        self.lbl_track.pack(anchor="w", pady=(10, 5))
        
        self.lbl_artist = ctk.CTkLabel(info, text="Unknown Artist", font=FONTS["body"], text_color=COLORS["text_dim"])
        self.lbl_artist.pack(anchor="w", pady=(0, 20))
        
        # Buttons
        btns = ctk.CTkFrame(info, fg_color="transparent")
        btns.pack(anchor="w")
        
        ctk.CTkButton(btns, text="⏮", width=40, fg_color=COLORS["bg_dark"]).pack(side="left", padx=5)
        self.btn_play = ctk.CTkButton(btns, text="▶", width=60, fg_color=COLORS["accent"], command=self.toggle_play)
        self.btn_play.pack(side="left", padx=5)
        ctk.CTkButton(btns, text="⏭", width=40, fg_color=COLORS["bg_dark"]).pack(side="left", padx=5)
        
    def _create_playlist(self):
        # List Header
        ctk.CTkLabel(self, text="  LOCAL LIBRARY", font=FONTS["h3"], text_color=COLORS["text_dim"]).grid(row=1, column=0, sticky="nw", padx=20)
        
        self.playlist_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.playlist_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(5, 20))
        
        self.refresh_library()
        
    def refresh_library(self):
        try:
            files = [f for f in os.listdir(self.music_dir) if f.endswith((".mp3", ".wav", ".flac"))]
            
            if not files:
                 ctk.CTkLabel(self.playlist_frame, text="No music found in ~/Music", text_color=COLORS["text_dim"]).pack(pady=20)
                 return

            for f in files:
                btn = ctk.CTkButton(self.playlist_frame, text=f"🎵  {f}", 
                                    fg_color="transparent", hover_color=COLORS["bg_card"],
                                    anchor="w", text_color=COLORS["text_main"], font=FONTS["body"],
                                    command=lambda t=f: self.play_track(t))
                btn.pack(fill="x", pady=2)
        except Exception as e:
            print(f"Music scan error: {e}")
            
    def play_track(self, track_name):
        self.current_track = track_name
        self.lbl_track.configure(text=track_name)
        self.playing = True
        self.btn_play.configure(text="⏸")
        # Actual audio logic would involve pygame.mixer.load() and play()
        
    def toggle_play(self):
        self.playing = not self.playing
        self.btn_play.configure(text="⏸" if self.playing else "▶")
