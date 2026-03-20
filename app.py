import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from src._LocalTranscribe import transcribe, get_path
import customtkinter
import threading


# ── Helper: redirect stdout/stderr into a CTkTextbox ──────────────────────
import re
_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')  # strip colour codes

class _ConsoleRedirector:
    """Redirects output exclusively to the in-app console panel."""
    def __init__(self, text_widget):
        self.widget = text_widget

    def write(self, text):
        clean = _ANSI_RE.sub('', text)        # strip ANSI colours
        if clean.strip() == '':
            return
        # Schedule UI update on the main thread
        try:
            self.widget.after(0, self._append, clean)
        except Exception:
            pass

    def _append(self, text):
        self.widget.configure(state='normal')
        self.widget.insert('end', text + ('\n' if not text.endswith('\n') else ''))
        self.widget.see('end')
        self.widget.configure(state='disabled')

    def flush(self):
        pass

# HuggingFace model IDs for non-standard models
HF_MODEL_MAP = {
    'KB Swedish (tiny)':   'KBLab/kb-whisper-tiny',
    'KB Swedish (base)':   'KBLab/kb-whisper-base',
    'KB Swedish (small)':  'KBLab/kb-whisper-small',
    'KB Swedish (medium)': 'KBLab/kb-whisper-medium',
    'KB Swedish (large)':  'KBLab/kb-whisper-large',
}



customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green
firstclick = True


def _set_app_icon(root):
    """Set app icon when supported, without crashing on unsupported platforms."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "images", "icon.ico")

    if not os.path.exists(icon_path):
        return

    try:
        root.iconbitmap(icon_path)
    except tk.TclError:
        # Some Linux Tk builds don't accept .ico for iconbitmap.
        pass


def _apply_display_scaling(root):
    """Auto-scale UI for high-resolution displays (e.g., 4K)."""
    try:
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        scale = min(screen_w / 1920.0, screen_h / 1080.0)
        scale = max(1.0, min(scale, 2.0))
        customtkinter.set_widget_scaling(scale)
        customtkinter.set_window_scaling(scale)
    except Exception:
        pass

class App:
    def __init__(self, master):
        self.master = master
        # Change font
        font = ('Roboto', 13, 'bold')  # Change the font and size here
        font_b = ('Roboto', 12)  # Change the font and size here
        # Folder Path
        path_frame = customtkinter.CTkFrame(master)
        path_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        customtkinter.CTkLabel(path_frame, text="Folder:", font=font).pack(side=tk.LEFT, padx=5)
        self.path_entry = customtkinter.CTkEntry(path_frame, width=50, font=font_b)
        self.path_entry.insert(0, os.path.join(os.getcwd(), 'sample_audio'))
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        customtkinter.CTkButton(path_frame, text="Browse", command=self.browse, font=font).pack(side=tk.LEFT, padx=5)
        # Language frame        
        #thanks to pommicket from Stackoverflow for this fix
        def on_entry_click(event):
            """function that gets called whenever entry is clicked"""        
            global firstclick
            if firstclick: # if this is the first time they clicked it
                firstclick = False
                self.language_entry.delete(0, "end") # delete all the text in the entry
        language_frame = customtkinter.CTkFrame(master)
        language_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        customtkinter.CTkLabel(language_frame, text="Language:", font=font).pack(side=tk.LEFT, padx=5)
        self.language_entry = customtkinter.CTkEntry(language_frame, width=50, font=('Roboto', 12, 'italic'))
        self.default_language_text = "Enter language (or ignore to auto-detect)"
        self.language_entry.insert(0, self.default_language_text)
        self.language_entry.bind('<FocusIn>', on_entry_click)
        self.language_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # Model frame
        models = ['tiny', 'tiny.en', 'base', 'base.en',
                  'small', 'small.en', 'medium', 'medium.en',
                  'large-v2', 'large-v3',
                  '───────────────',
                  'KB Swedish (tiny)', 'KB Swedish (base)',
                  'KB Swedish (small)', 'KB Swedish (medium)',
                  'KB Swedish (large)']
        model_frame = customtkinter.CTkFrame(master)
        model_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        customtkinter.CTkLabel(model_frame, text="Model:", font=font).pack(side=tk.LEFT, padx=5)
        # ComboBox frame
        self.model_combobox = customtkinter.CTkComboBox(
            model_frame, width=50, state="readonly",
            values=models, font=font_b)
        self.model_combobox.set('medium')  # Set the default value
        self.model_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # Timestamps toggle
        ts_frame = customtkinter.CTkFrame(master)
        ts_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        self.timestamps_var = tk.BooleanVar(value=True)
        self.timestamps_switch = customtkinter.CTkSwitch(
            ts_frame, text="Include timestamps in transcription",
            variable=self.timestamps_var, font=font_b)
        self.timestamps_switch.pack(side=tk.LEFT, padx=5)
        # Progress Bar
        self.progress_bar = ttk.Progressbar(master, length=200, mode='indeterminate')
        # Button actions frame
        button_frame = customtkinter.CTkFrame(master)
        button_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        self.transcribe_button = customtkinter.CTkButton(button_frame, text="Transcribe", command=self.start_transcription, font=font)
        self.transcribe_button.pack(side=tk.LEFT, padx=5, pady=10, fill=tk.X, expand=True)
        customtkinter.CTkButton(button_frame, text="Quit", command=master.quit, font=font).pack(side=tk.RIGHT, padx=5, pady=10, fill=tk.X, expand=True)

        # ── Embedded console / log panel ──────────────────────────────────
        log_label = customtkinter.CTkLabel(master, text="Console output", font=font, anchor='w')
        log_label.pack(fill=tk.X, padx=12, pady=(8, 0))
        self.log_box = customtkinter.CTkTextbox(master, height=220, font=('Consolas', 14),
                                                 wrap='word', state='disabled',
                                                 fg_color='#1e1e1e', text_color='#e0e0e0')
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2, 10))

        # Redirect stdout & stderr into the log panel (no backend console)
        sys.stdout = _ConsoleRedirector(self.log_box)
        sys.stderr = _ConsoleRedirector(self.log_box)

        # Welcome message (shown after redirect so it appears in the panel)
        print("Welcome to Local Transcribe with Whisper! \U0001f600")
        print("Transcriptions will be saved automatically.")
        print("─" * 46)
    # Helper functions
    # Browsing
    def browse(self):
        initial_dir = os.getcwd()
        folder_path = filedialog.askdirectory(initialdir=initial_dir)
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, folder_path)
    # Start transcription
    def start_transcription(self):
        # Disable transcribe button
        self.transcribe_button.configure(state=tk.DISABLED)
        # Start a new thread for the transcription process
        threading.Thread(target=self.transcribe_thread).start()
    # Threading
    def transcribe_thread(self):
        path = self.path_entry.get()
        model_display = self.model_combobox.get()
        # Ignore the visual separator
        if model_display.startswith('─'):
            messagebox.showinfo("Invalid selection", "Please select a model, not the separator line.")
            self.transcribe_button.configure(state=tk.NORMAL)
            return
        model = HF_MODEL_MAP.get(model_display, model_display)
        language = self.language_entry.get()
        # Auto-set Swedish for KB models
        is_kb_model = model_display.startswith('KB Swedish')
        # Check if the language field has the default text or is empty
        if is_kb_model:
            language = 'sv'
        elif language == self.default_language_text or not language.strip():
            language = None  # This is the same as passing nothing
        verbose = True   # always show transcription progress in the console panel
        timestamps = self.timestamps_var.get()
        # Show progress bar
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        self.progress_bar.start()
        # Setting path and files
        glob_file = get_path(path)
        #messagebox.showinfo("Message", "Starting transcription!")
        # Start transcription
        try:
            output_text = transcribe(path, glob_file, model, language, verbose, timestamps)
        except UnboundLocalError:
            messagebox.showinfo("Files not found error!", 'Nothing found, choose another folder.')
            pass
        except ValueError:
            messagebox.showinfo("Invalid language name, you might have to clear the default text to continue!")
        # Hide progress bar
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        # Enable transcribe button
        self.transcribe_button.configure(state=tk.NORMAL)
        # Recover output text
        try:
            messagebox.showinfo("Finished!", output_text)
        except UnboundLocalError:
            pass

if __name__ == "__main__":
    # Setting custom themes
    root = customtkinter.CTk()
    _apply_display_scaling(root)
    root.title("Local Transcribe with Whisper")
    # Geometry — taller to accommodate the embedded console panel
    width, height = 550, 560
    root.geometry('{}x{}'.format(width, height))
    root.minsize(450, 480)
    # Icon (best-effort; ignored on platforms/builds without .ico support)
    _set_app_icon(root)
    # Run
    app = App(root)
    root.mainloop()
