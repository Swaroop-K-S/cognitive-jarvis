import customtkinter as ctk
import threading
from PIL import Image
from jarvis.ui.theme import COLORS, FONTS

class VisionPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
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
