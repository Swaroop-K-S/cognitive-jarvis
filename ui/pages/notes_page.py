import customtkinter as ctk
import os
from jarvis.ui.theme import COLORS, FONTS

class NotesPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.notes_dir = os.path.join("data", "notes")
        os.makedirs(self.notes_dir, exist_ok=True)
        
        # Grid layout: List (1/3) | Editor (2/3)
        self.grid_columnconfigure(0, weight=1) # List
        self.grid_columnconfigure(1, weight=3) # Editor
        self.grid_rowconfigure(0, weight=1)
        
        self.current_note_file = None
        
        self._create_list_panel()
        self._create_editor_panel()
        self.refresh_list()
        
    def _create_list_panel(self):
        panel = ctk.CTkFrame(self, fg_color=COLORS["bg_card"])
        panel.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        
        # Header
        head = ctk.CTkFrame(panel, fg_color="transparent", height=40)
        head.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(head, text="📝 NOTES", font=FONTS["h3"], text_color=COLORS["text_dim"]).pack(side="left")
        
        ctk.CTkButton(head, text="+", width=30, height=30, 
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      command=self.new_note).pack(side="right")
        
        # Scrollable List
        self.note_list = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        self.note_list.pack(fill="both", expand=True, padx=5, pady=5)
        
    def _create_editor_panel(self):
        panel = ctk.CTkFrame(self, fg_color=COLORS["bg_card"])
        panel.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        
        # Title Entry
        self.title_var = ctk.StringVar()
        self.title_entry = ctk.CTkEntry(panel, textvariable=self.title_var, 
                                        font=FONTS["h2"], border_width=0, 
                                        fg_color="transparent", placeholder_text="Note Title...")
        self.title_entry.pack(fill="x", padx=20, pady=(20, 10))
        
        # Text Area
        self.editor = ctk.CTkTextbox(panel, font=FONTS["body"], 
                                     fg_color="transparent", text_color=COLORS["text_main"],
                                     wrap="word")
        self.editor.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Save Trigger
        self.editor.bind("<KeyRelease>", self.auto_save)
        self.title_entry.bind("<KeyRelease>", self.auto_save)
        
    def refresh_list(self):
        # Clear
        for widget in self.note_list.winfo_children():
            widget.destroy()
            
        # Scan dir
        files = [f for f in os.listdir(self.notes_dir) if f.endswith(".txt")]
        for f in files:
            name = f.replace(".txt", "").replace("_", " ").title()
            btn = ctk.CTkButton(self.note_list, text=name, 
                                fg_color="transparent", hover_color=COLORS["bg_dark"],
                                anchor="w", text_color=COLORS["text_main"],
                                command=lambda fn=f: self.load_note(fn))
            btn.pack(fill="x", pady=2)
            
    def new_note(self):
        self.current_note_file = None
        self.title_var.set("")
        self.editor.delete("1.0", "end")
        self.title_entry.focus()
        
    def load_note(self, filename):
        self.current_note_file = filename
        path = os.path.join(self.notes_dir, filename)
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Assume first line is title if format allows, but for simplicity:
            # We use filename as title proxy or separate logic
            title = filename.replace(".txt", "").replace("_", " ").title()
            
            self.title_var.set(title)
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", content)
        except Exception as e:
            print(f"Error loading note: {e}")
            
    def auto_save(self, event=None):
        title = self.title_var.get().strip()
        content = self.editor.get("1.0", "end-1c")
        
        if not title: return
        
        # Filename safe
        safe_name = "".join([c for c in title if c.isalnum() or c in " -_"]).strip().replace(" ", "_").lower() + ".txt"
        path = os.path.join(self.notes_dir, safe_name)
        
        # If renamed, delete old? (Complexity skip: Just create new for now to avoid data loss bugs in mvp)
        # Proper way: Track if renamed
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
            
        if self.current_note_file != safe_name:
            self.current_note_file = safe_name
            self.refresh_list()
