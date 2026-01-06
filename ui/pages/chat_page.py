import customtkinter as ctk
from jarvis.ui.theme import COLORS, FONTS
from jarvis.ui.components.voice_visualizer import VoiceVisualizer
from jarvis.voice.audio_stream import AudioStreamAnalyzer

class ChatPage(ctk.CTkFrame):
    def __init__(self, parent, send_callback):
        super().__init__(parent, fg_color="transparent")
        self.send_callback = send_callback
        
        # Grid layout
        self.grid_rowconfigure(1, weight=1) # Chat history grows
        self.grid_columnconfigure(0, weight=1)
        
        self._create_header()
        self._create_chat_area()
        self._create_input_area()
        
        # Audio Stream
        self.audio_stream = AudioStreamAnalyzer()
        self.visualizer.attach_stream(self.audio_stream)
        
    def _create_header(self):
        head = ctk.CTkFrame(self, height=50, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        ctk.CTkLabel(head, text="💬 Live Neural Link", font=FONTS["h2"], text_color=COLORS["text_dim"]).pack(side="left")
        ctk.CTkButton(head, text="🗑️ Clear Memory", width=100, height=30, 
                      fg_color=COLORS["bg_card"], hover_color=COLORS["text_error"],
                      font=FONTS["tiny"], command=self.clear_chat).pack(side="right")

    def _create_chat_area(self):
        self.chat_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.chat_scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=0)
        
        # Welcome message
        self.add_message("BRO", "Systems Online. Neural Link Active. 🚀")

    def _create_input_area(self):
        input_container = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=60, corner_radius=20)
        input_container.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        
        # Mic Button
        self.mic_btn = ctk.CTkButton(input_container, text="🎤", width=40, height=40, corner_radius=20,
                                     fg_color=COLORS["mic_inactive"], hover_color=COLORS["text_error"],
                                     font=("Segoe UI", 16), command=self.toggle_mic)
        self.mic_btn.pack(side="left", padx=10, pady=10)
        
        # Audio Visualizer (Hidden by default or acts as spacer)
        self.visualizer = VoiceVisualizer(input_container, width=100, height=40, bg=COLORS["bg_card"])
        self.visualizer.pack(side="left", padx=5)
        
        # Entry
        self.entry = ctk.CTkEntry(input_container, placeholder_text="Command the system...", 
                                  font=FONTS["body"], height=40, border_width=0, fg_color="transparent",
                                  text_color=COLORS["text_main"])
        self.entry.pack(side="left", fill="x", expand=True, padx=10)
        self.entry.bind("<Return>", lambda e: self.send())
        
        # Send Button
        send_btn = ctk.CTkButton(input_container, text="➤", width=40, height=40, corner_radius=20,
                                 fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                                 font=("Segoe UI", 16), command=self.send)
        send_btn.pack(side="right", padx=10)

    def add_message(self, sender, text, animate=False):
        # Bubble Container
        bubble_frame = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        bubble_frame.pack(fill="x", pady=5)
        
        is_me = sender == "You"
        bg = COLORS["accent_dim"] if is_me else COLORS["bg_card"]
        align = "right" if is_me else "left"
        text_color = COLORS["text_main"]
        
        # Spacer for alignment
        if is_me:
            ctk.CTkFrame(bubble_frame, fg_color="transparent").pack(side="left", expand=True, fill="x")
        
        # Actual Bubble Frame
        msg_frame = ctk.CTkFrame(bubble_frame, fg_color=bg, corner_radius=15, border_width=1 if not is_me else 0, border_color=COLORS["border"])
        msg_frame.pack(side=align, padx=10, fill="y") # fill=y to match height
        
        if not is_me:
             ctk.CTkFrame(bubble_frame, fg_color="transparent").pack(side="right", expand=True, fill="x")

        # Sender Label (Tiny)
        # ctk.CTkLabel(msg_frame, text=sender, font=FONTS["tiny"], text_color=COLORS["text_dim"]).pack(anchor="w", padx=10, pady=(5,0))

        # Text Content (Textbox for better wrapping/copying)
        # Calculate rough height
        lines = text.count('\n') + (len(text) // 60) + 1
        height = min(lines * 20 + 20, 400) # Cap height, enable scroll if needed
        
        textbox = ctk.CTkTextbox(msg_frame, font=FONTS["body"], text_color=text_color, 
                                 fg_color="transparent", wrap="word", height=height, width=400)
        textbox.pack(padx=10, pady=10)
        
        if animate and not is_me:
            self._type_text(textbox, text)
        else:
            textbox.insert("1.0", text)
        
        textbox.configure(state="disabled") # Read-only
        
        # Scroll down
        self.update_idletasks()
        self.chat_scroll._parent_canvas.yview_moveto(1.0)
        
    def _type_text(self, textbox, text, index=0):
        if index < len(text):
            textbox.insert(f"end-1c", text[index]) # insert before disabled
            # textbox.configure(state="disabled") # Re-disable? No, leave enabled during typing? 
            # Actually CTKTextbox needs to be enabled to insert.
            self.after(10, self._type_text, textbox, text, index+1)
        else:
            textbox.configure(state="disabled")
            self.chat_scroll._parent_canvas.yview_moveto(1.0)

    def send(self):
        text = self.entry.get().strip()
        if text:
            self.entry.delete(0, "end")
            self.add_message("You", text)
            self.send_callback(text)

    def toggle_mic(self):
        # Visual toggle, logic handled in controller
        active = not self.visualizer.active
        self.visualizer.set_active(active)
        
        if active:
            self.mic_btn.configure(fg_color=COLORS["text_error"])
            self.audio_stream.start()
        else:
            self.mic_btn.configure(fg_color=COLORS["mic_inactive"])
            self.audio_stream.stop()
        
    def clear_chat(self):
        for widget in self.chat_scroll.winfo_children():
            widget.destroy()
