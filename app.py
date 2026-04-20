import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from src._LocalTranscribe import transcribe, get_path
import customtkinter
import threading
import queue


# ── Helper: redirect stdout/stderr into a CTkTextbox ──────────────────────
import re
_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')  # strip colour codes

class _ConsoleRedirector:
    """Tee Python output to an in-app log queue.

    The real C-level stdout/stderr file descriptors are left untouched
    so that native libraries (ctranslate2 etc.) can write to them
    without crashing. Only Python-level print() / sys.stdout.write()
    is intercepted and forwarded to the UI queue.
    """
    def __init__(self, log_queue, real_stream):
        self._log_queue = log_queue
        self._real = real_stream

    def write(self, text):
        try:
            self._real.write(text)
        except Exception:
            pass
        clean = _ANSI_RE.sub('', text)
        if not clean:
            return
        try:
            self._log_queue.put_nowait(clean)
        except Exception:
            pass

    def flush(self):
        try:
            self._real.flush()
        except Exception:
            pass

    def fileno(self):
        return self._real.fileno()

# HuggingFace model IDs for non-standard models
HF_MODEL_MAP = {
    'KB Swedish (tiny)':   'KBLab/kb-whisper-tiny',
    'KB Swedish (base)':   'KBLab/kb-whisper-base',
    'KB Swedish (small)':  'KBLab/kb-whisper-small',
    'KB Swedish (medium)': 'KBLab/kb-whisper-medium',
    'KB Swedish (large)':  'KBLab/kb-whisper-large',
}

WINDOWS_CPU_HINT = ' (CPU on Windows)'



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
        self.log_queue = queue.Queue()
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
        models = [f'tiny{WINDOWS_CPU_HINT}', f'tiny.en{WINDOWS_CPU_HINT}', 'base', 'base.en',
                  'small', 'small.en', 'medium', 'medium.en',
                  'large-v2', 'large-v3',
                  '───────────────',
              f'KB Swedish (tiny){WINDOWS_CPU_HINT}', 'KB Swedish (base)',
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
        # Output format toggles
        ts_frame = customtkinter.CTkFrame(master)
        ts_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        self.ts_with_var = tk.BooleanVar(value=True)
        self.ts_plain_var = tk.BooleanVar(value=False)
        customtkinter.CTkSwitch(
            ts_frame, text="With timestamps",
            variable=self.ts_with_var, font=font_b).pack(side=tk.LEFT, padx=5)
        customtkinter.CTkSwitch(
            ts_frame, text="Without timestamps",
            variable=self.ts_plain_var, font=font_b).pack(side=tk.LEFT, padx=15)
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

        # Redirect stdout & stderr into the log panel.
        # Keep real file-descriptor streams alive so native C libraries don't crash.
        _real_stdout = sys.__stdout__
        _real_stderr = sys.__stderr__
        sys.stdout = _ConsoleRedirector(self.log_queue, _real_stdout)
        sys.stderr = _ConsoleRedirector(self.log_queue, _real_stderr)
        self.master.after(50, self._drain_log_queue)

        # Welcome message (shown after redirect so it appears in the panel)
        print("Welcome to Local Transcribe with Whisper! \U0001f600")
        print("Transcriptions will be saved automatically.")
        print("─" * 46)

    def _drain_log_queue(self):
        updated = False
        chunks = []
        while True:
            try:
                chunks.append(self.log_queue.get_nowait())
            except queue.Empty:
                break

        if chunks:
            updated = True
            self.log_box.configure(state='normal')
            for chunk in chunks:
                self.log_box.insert('end', chunk.replace('\r', '\n'))
            self.log_box.see('end')
            self.log_box.configure(state='disabled')

        try:
            self.master.after(50, self._drain_log_queue)
        except tk.TclError:
            if updated:
                return

    def _finish_transcription(self, output_text=None, dialog_title=None, dialog_message=None, is_error=False):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.transcribe_button.configure(state=tk.NORMAL)

        if dialog_title and dialog_message:
            dialog = messagebox.showerror if is_error else messagebox.showinfo
            dialog(dialog_title, dialog_message)
            return

        if output_text:
            messagebox.showinfo("Finished!", output_text)

    def _get_transcription_request(self):
        path = self.path_entry.get()
        model_display = self.model_combobox.get()
        if model_display.startswith('─'):
            messagebox.showinfo("Invalid selection", "Please select a model, not the separator line.")
            return None

        model_key = model_display.replace(WINDOWS_CPU_HINT, '')
        model = HF_MODEL_MAP.get(model_key, model_key)
        language = self.language_entry.get()
        is_kb_model = model_key.startswith('KB Swedish')
        if is_kb_model:
            language = 'sv'
        elif language == self.default_language_text or not language.strip():
            language = None

        save_timestamps = self.ts_with_var.get()
        save_plain = self.ts_plain_var.get()
        if not save_timestamps and not save_plain:
            messagebox.showinfo("No output selected", "Enable at least one output format (with or without timestamps).")
            return None

        glob_file = get_path(path)
        return path, glob_file, model, language, save_timestamps, save_plain

    # Helper functions
    # Browsing
    def browse(self):
        initial_dir = os.getcwd()
        folder_path = filedialog.askdirectory(initialdir=initial_dir)
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, folder_path)
    # Start transcription
    def start_transcription(self):
        request = self._get_transcription_request()
        if request is None:
            return

        self.transcribe_button.configure(state=tk.DISABLED)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        self.progress_bar.start()
        threading.Thread(target=self.transcribe_thread, args=request, daemon=True).start()

    # Threading
    def transcribe_thread(self, path, glob_file, model, language, save_timestamps, save_plain):
        verbose = True   # always show transcription progress in the console panel
        try:
            output_text = transcribe(path, glob_file, model, language, verbose,
                                      save_timestamps=save_timestamps, save_plain=save_plain)
        except UnboundLocalError:
            self.master.after(
                0,
                self._finish_transcription,
                None,
                "Files not found error!",
                'Nothing found, choose another folder.',
                False,
            )
            return
        except ValueError:
            self.master.after(
                0,
                self._finish_transcription,
                None,
                "Error",
                "Invalid language name, you might have to clear the default text to continue!",
                False,
            )
            return
        except Exception as exc:
            print(f"⚠  Unexpected error: {exc}")
            self.master.after(
                0,
                self._finish_transcription,
                None,
                "Error",
                f"Something went wrong:\n{exc}",
                True,
            )
            return

        self.master.after(0, self._finish_transcription, output_text)

if __name__ == "__main__":
    # ── Global crash handler — log to file so GUI redirect can't hide it ──
    import traceback as _tb
    _CRASH_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crash.log')

    def _log_unhandled(exc_type, exc_value, exc_tb):
        msg = ''.join(_tb.format_exception(exc_type, exc_value, exc_tb))
        try:
            with open(_CRASH_LOG, 'a', encoding='utf-8') as f:
                f.write(msg + '\n')
        except Exception:
            pass
        sys.__stderr__.write(msg)

    sys.excepthook = _log_unhandled

    def _thread_excepthook(args):
        _log_unhandled(args.exc_type, args.exc_value, args.exc_traceback)

    threading.excepthook = _thread_excepthook

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
