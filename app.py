import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from src._LocalTranscribe import transcribe, get_path
import customtkinter
import threading
from colorama import Back
import colorama
colorama.init(autoreset=True)
import os 

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green
firstclick = True

class App:
    def __init__(self, master):
        print(Back.CYAN + "Welcome to Local Transcribe with Whisper!\U0001f600\nCheck back here to see some output from your transcriptions.\nDon't worry, they will also be saved on the computer!\U0001f64f")
        self.master = master
        font = ('Roboto', 13, 'bold')  
        font_b = ('Roboto', 12)  

        # Folder selection frame
        path_frame = customtkinter.CTkFrame(master)
        path_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        customtkinter.CTkLabel(path_frame, text="Folder:", font=font).pack(side=tk.LEFT, padx=5)
        self.path_entry = customtkinter.CTkEntry(path_frame, width=50, font=font_b)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        customtkinter.CTkButton(path_frame, text="Browse", command=self.browse, font=font).pack(side=tk.LEFT, padx=5)

        # Max segment duration frame
        max_duration_frame = customtkinter.CTkFrame(master)
        max_duration_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        customtkinter.CTkLabel(max_duration_frame, text="Max Segment (sec):", font=font).pack(side=tk.LEFT, padx=5)
        self.max_duration_entry = customtkinter.CTkEntry(max_duration_frame, width=50, placeholder_text="0 = no limit", font=font_b)
        self.max_duration_entry.pack(side=tk.LEFT, fill=tk.X, expand=True) 

        # **New** Minimum segment duration frame
        min_duration_frame = customtkinter.CTkFrame(master)
        min_duration_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        customtkinter.CTkLabel(min_duration_frame, text="Min Segment (sec):", font=font).pack(side=tk.LEFT, padx=5)
        self.min_duration_entry = customtkinter.CTkEntry(min_duration_frame, width=50, placeholder_text="0 = no limit", font=font_b)
        self.min_duration_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Language frame
        def on_entry_click(event):
            """function that gets called whenever entry is clicked"""        
            global firstclick
            if firstclick:
                firstclick = False
                self.language_entry.delete(0, "end") 
        language_frame = customtkinter.CTkFrame(master)
        language_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        customtkinter.CTkLabel(language_frame, text="Language:", font=font).pack(side=tk.LEFT, padx=5)
        self.language_entry = customtkinter.CTkEntry(language_frame, width=50, font=('Roboto', 12, 'italic'))
        self.default_language_text = "Enter language (or ignore to auto-detect)"
        self.language_entry.insert(0, self.default_language_text)
        self.language_entry.bind('<FocusIn>', on_entry_click)
        self.language_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Model frame
        models = ['base.en', 'base', 'small.en', 'small', 'medium.en', 'medium', 'large']
        model_frame = customtkinter.CTkFrame(master)
        model_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        customtkinter.CTkLabel(model_frame, text="Model:", font=font).pack(side=tk.LEFT, padx=5)
        self.model_combobox = customtkinter.CTkComboBox(model_frame, width=50, state="readonly",
                                                        values=models, font=font_b)
        self.model_combobox.set(models[1])  
        self.model_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Verbose frame
        verbose_frame = customtkinter.CTkFrame(master)
        verbose_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        self.verbose_var = tk.BooleanVar()
        customtkinter.CTkCheckBox(verbose_frame, text="Output transcription to terminal", variable=self.verbose_var, font=font).pack(side=tk.LEFT, padx=5)

        # Output Format Frame
        output_frame = customtkinter.CTkFrame(master)
        output_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        self.srt_var = tk.BooleanVar()
        customtkinter.CTkCheckBox(output_frame, text="Export as SRT", variable=self.srt_var, font=font).pack(side=tk.LEFT, padx=5)

        # Progress Bar
        self.progress_bar = ttk.Progressbar(master, length=200, mode='indeterminate')

        # Button actions frame
        button_frame = customtkinter.CTkFrame(master)
        button_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        self.transcribe_button = customtkinter.CTkButton(button_frame, text="Transcribe", command=self.start_transcription, font=font)
        self.transcribe_button.pack(side=tk.LEFT, padx=5, pady=10, fill=tk.X, expand=True)
        customtkinter.CTkButton(button_frame, text="Quit", command=master.quit, font=font).pack(side=tk.RIGHT, padx=5, pady=10, fill=tk.X, expand=True)

    # Helper functions
    def browse(self):
        initial_dir = os.getcwd()
        folder_path = filedialog.askdirectory(initialdir=initial_dir)
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, folder_path)

    def start_transcription(self):
        # Disable transcribe button
        self.transcribe_button.configure(state=tk.DISABLED)
        # Start a new thread for the transcription process
        threading.Thread(target=self.transcribe_thread).start()

    def transcribe_thread(self):
        path = self.path_entry.get()
        model = self.model_combobox.get()
        language = self.language_entry.get()
        srt_format = self.srt_var.get()
        if language == self.default_language_text or not language.strip():
            language = None
        verbose = self.verbose_var.get()

        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        self.progress_bar.start()

        glob_file = get_path(path)
        try:
            max_duration_str = self.max_duration_entry.get().strip()
            max_duration = float(max_duration_str) if max_duration_str else 0
            max_duration = max_duration if max_duration > 0 else None
        except ValueError:
            max_duration = None 
            messagebox.showwarning("Invalid Duration", "Using default segment duration")

        try:
            # **New** Read minimum segment duration
            min_duration_str = self.min_duration_entry.get().strip()
            min_duration = float(min_duration_str) if min_duration_str else 0
            # Use 0 if no valid minimum is provided
            min_duration = min_duration if min_duration > 0 else 0
        except ValueError:
            min_duration = 0 
            messagebox.showwarning("Invalid Duration", "Using default segment minimum duration")

        try:
            output_text = transcribe(path, glob_file, model, language, verbose, max_duration, srt_format, min_segment_duration=min_duration)
        except UnboundLocalError:
            messagebox.showinfo("Files not found error!", 'Nothing found, choose another folder.')
            output_text = ""
        except ValueError:
            messagebox.showinfo("Invalid language name", "You might have to clear the default text to continue!")
            output_text = ""

        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.transcribe_button.configure(state=tk.NORMAL)
        try:
            messagebox.showinfo("Finished!", output_text)
        except UnboundLocalError:
            pass

if __name__ == "__main__":
    root = customtkinter.CTk()
    root.title("Local Transcribe with Whisper")
    width, height = 450,450
    root.geometry('{}x{}'.format(width, height))
    root.iconbitmap('images/icon.ico')
    app = App(root)
    root.mainloop()