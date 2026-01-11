import customtkinter as ctk
import threading
from PIL import Image
from jarvis.ui.theme import COLORS, FONTS

class VisionPage(ctk.CTkFrame):
    def __init__(self, parent, brain=None):
        super().__init__(parent, fg_color="transparent")
        
        self.brain = brain
        # Init autonomous copilot if brain available
        if self.brain:
            try:
                from jarvis.tools.screen_copilot import get_copilot
                get_copilot(self.brain)
            except Exception as e:
                print(f"Copilot Init Error: {e}")
                
        # Init Face Sentry
        try:
            from jarvis.vision.face_detect import FaceSentry
            self.sentry = FaceSentry()
        except Exception as e:
            print(f"Sentry Init Error: {e}")
            self.sentry = None
            
        self.sentry_active = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Result expands
        
        self._create_header()
        self._create_controls()
        self._create_display_area()
        
    def _create_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        ctk.CTkLabel(head, text="👁️ VISUAL CORTEX", font=FONTS["h2"], text_color=COLORS["text_dim"]).pack(side="left")

    def _create_controls(self):
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        # Analyze Button
        btn_analyze = ctk.CTkButton(ctrl, text="📸 ANALYZE SCREEN", width=180, height=40,
                                   fg_color=COLORS["text_error"], hover_color="#C03949", font=FONTS["body_bold"],
                                   command=lambda: self.run_vision("analyze"))
        btn_analyze.pack(side="left", padx=(0, 10))
        
        # OCR Button
        btn_ocr = ctk.CTkButton(ctrl, text="📝 READ TEXT (OCR)", width=180, height=40,
                               fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], font=FONTS["body_bold"],
                               command=lambda: self.run_vision("ocr"))
        btn_ocr.pack(side="left")

        # Auto Toggle
        self.copilot_var = ctk.StringVar(value="off")
        self.switch_copilot = ctk.CTkSwitch(ctrl, text="🤖 AUTO COPILOT", variable=self.copilot_var,
                                            onvalue="on", offvalue="off", font=FONTS["body_bold"],
                                            command=self.toggle_copilot)
        self.switch_copilot.pack(side="right", padx=10)
        
        # Face ID Toggle
        self.sentry_var = ctk.StringVar(value="off")
        self.switch_sentry = ctk.CTkSwitch(ctrl, text="🛡️ FACE ID", variable=self.sentry_var,
                                            onvalue="on", offvalue="off", font=FONTS["body_bold"],
                                            command=self.toggle_sentry, progress_color=COLORS["text_success"])
        self.switch_sentry.pack(side="right", padx=10)
        
    def _create_display_area(self):
        # Preview Image
        self.preview_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], height=300)
        self.preview_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.preview_frame.pack_propagate(False) # Fixed height for preview
        
        self.lbl_preview = ctk.CTkLabel(self.preview_frame, text="[No Signal]", text_color=COLORS["text_dim"])
        self.lbl_preview.pack(expand=True, fill="both")
        
        # Text Result
        self.txt_result = ctk.CTkTextbox(self, font=("Consolas", 14), fg_color=COLORS["bg_card"], text_color=COLORS["text_main"])
        self.txt_result.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.grid_rowconfigure(3, weight=1)

    def run_vision(self, action):
        self.txt_result.delete("0.0", "end")
        self.txt_result.insert("0.0", "Processing visual stream... please wait...")
        self.lbl_preview.configure(image=None, text="Capturing...")
        
        threading.Thread(target=self._process_vision, args=(action,), daemon=True).start()
        
    def _process_vision(self, action):
        try:
            from jarvis.tools.vision import analyze_screen, read_screen_text, save_screenshot
            
            # 1. Capture & Show Preview
            # capture_path is usually "Snapshot saved: C:\\...\\image.png"
            snap_res = save_screenshot()
            
            if "❌" not in snap_res:
                path = snap_res.split(": ")[1].strip()
                self.after(0, lambda: self._show_preview(path))
            
            # 2. Process
            result = ""
            if action == "analyze":
                result = analyze_screen()
            elif action == "ocr":
                result = read_screen_text()
                
            self.after(0, lambda: self._update_result(result))
            
        except Exception as e:
            self.after(0, lambda: self._update_result(f"Visual Cortex Error: {e}"))
            
    def _show_preview(self, path):
        try:
            img = Image.open(path)
            # Aspect ratio resize
            base_height = 280
            h_percent = (base_height / float(img.size[1]))
            w_size = int((float(img.size[0]) * float(h_percent)))
            img = img.resize((w_size, base_height), Image.Resampling.LANCZOS)
            
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self.lbl_preview.configure(image=ctk_img, text="")
        except Exception as e:
            print(f"Preview Error: {e}")
            self.lbl_preview.configure(text="[Preview Load Failed]")

    def _update_result(self, text):
        self.txt_result.delete("0.0", "end")
        self.txt_result.insert("0.0", text)

    def toggle_copilot(self):
        val = self.copilot_var.get()
        self.txt_result.delete("0.0", "end")
        
        try:
            from jarvis.tools.screen_copilot import enable_screen_copilot, disable_screen_copilot
            
            if val == "on":
                msg = enable_screen_copilot()
                self.txt_result.insert("0.0", f"CAPTURING...\n{msg}\n\n(I am now watching the screen in the background)")
            else:
                msg = disable_screen_copilot()
                self.txt_result.insert("0.0", msg)
        except Exception as e:
            self.txt_result.insert("0.0", f"Error toggling copilot: {e}")
            
    def toggle_sentry(self):
        if self.sentry_var.get() == "on":
            self.sentry_active = True
            threading.Thread(target=self._run_sentry_loop, daemon=True).start()
        else:
            self.sentry_active = False
            self.lbl_preview.configure(image=None, text="Sentry Deactivated")

    def _run_sentry_loop(self):
        """Webcam loop for Face ID."""
        import cv2
        from PIL import Image
        from jarvis.voice.tts import say
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            self.lbl_preview.configure(text="[Camera Failed]")
            return

        self.txt_result.delete("0.0", "end")
        self.txt_result.insert("0.0", "🛡️ SENTRY MODE ACTIVE\nScanning biometric signatures...")
        
        try:
            while self.sentry_active and cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                
                # Face Detection
                if self.sentry:
                    name, conf = self.sentry.process_frame(frame)
                    
                    # Draw Overlay
                    if name:
                        color = (0, 255, 0) if name == "Boss" else (0, 0, 255)
                        cv2.putText(frame, f"TARGET: {name.upper()}", (30, 50), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                        
                        # Greeting Trigger
                        if name == "Boss" and conf > 0.8:
                            # Verify if we should greet (FaceSentry handles cooldown internally, 
                            # but process_frame returns name only if verified time check passed? 
                            # Wait, process_frame logic handles 'last_seen'. 
                            # Actually, I should trigger voice here if it's a FRESH detection)
                            # The logic in FaceSentry updates last_seen but returns name always...
                            # Let's fix process_frame logic in previous step or handle here.
                            # Ah, looking at FaceSentry code: 
                            # "if best_match == 'Boss' and (time.time() - self.last_seen_boss > self.greeting_cooldown): return 'Boss'..."
                            # So it returns 'Boss' properly.
                            # Wait, process_frame returns 'Boss' EVERY FRAME if matches.
                            # The cooldown was inside the return. 
                            # Let's rely on simple state diff here.
                            pass
                        
                        if name == "Boss" and self.sentry.last_seen_boss == 0:
                             # First time detection hack
                             say(f"Welcome back, Boss.")
                             self.sentry.last_seen_boss = time.time()
                        elif name == "Boss" and (time.time() - self.sentry.last_seen_boss > 300):
                             say("Boss detected.") # Re-greet
                             self.sentry.last_seen_boss = time.time()
                
                # Convert to CTkImage
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                
                # Resize for preview
                mw, mh = 400, 300
                img.thumbnail((mw, mh))
                
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                
                self.after(0, lambda: self.lbl_preview.configure(image=ctk_img, text=""))
                time.sleep(0.03) # ~30fps
                
        except Exception as e:
            print(f"Sentry Loop Error: {e}")
        finally:
            cap.release()
            self.lbl_preview.configure(image=None, text="Sentry Off")
