import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from transcribe import transcribe
from ttkthemes import ThemedTk
import whisper 
import numpy as np
import glob, os


class App:
    def __init__(self, master):
        self.master = master
        master.title("Local Transcribe")

        #style = ttk.Style()
        #style.configure('TLabel', font=('Arial', 10), padding=10)
        #style.configure('TEntry', font=('Arial', 10), padding=10)
        #style.configure('TButton', font=('Arial', 10), padding=10)
        #style.configure('TCheckbutton', font=('Arial', 10), padding=10)

        # Folder Path
        path_frame = ttk.Frame(master, padding=10)
        path_frame.pack(fill=tk.BOTH)
        path_label = ttk.Label(path_frame, text="Folder Path:")
        path_label.pack(side=tk.LEFT, padx=5)
        self.path_entry = ttk.Entry(path_frame, width=50)
        self.path_entry.insert(10, 'sample_audio/')
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        browse_button = ttk.Button(path_frame, text="Browse", command=self.browse)
        browse_button.pack(side=tk.LEFT, padx=5)

        # File Type
        file_type_frame = ttk.Frame(master, padding=10)
        file_type_frame.pack(fill=tk.BOTH)
        file_type_label = ttk.Label(file_type_frame, text="File Type:")
        file_type_label.pack(side=tk.LEFT, padx=5)
        self.file_type_entry = ttk.Entry(file_type_frame, width=50)
        self.file_type_entry.insert(10, 'ogg')
        self.file_type_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Model
        model_frame = ttk.Frame(master, padding=10)
        model_frame.pack(fill=tk.BOTH)
        model_label = ttk.Label(model_frame, text="Model:")
        model_label.pack(side=tk.LEFT, padx=5)
        self.model_entry = ttk.Entry(model_frame, width=50)
        self.model_entry.insert(10, 'small')
        self.model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Language (currently disabled)
        #language_frame = ttk.Frame(master, padding=10)
        #language_frame.pack(fill=tk.BOTH)
        #language_label = ttk.Label(language_frame, text="Language:")
        #language_label.pack(side=tk.LEFT, padx=5)
        #self.language_entry = ttk.Entry(language_frame, width=50)
        #self.language_entry.insert(10, np.nan)
        #self.language_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Verbose
        verbose_frame = ttk.Frame(master, padding=10)
        verbose_frame.pack(fill=tk.BOTH)
        self.verbose_var = tk.BooleanVar()
        verbose_checkbutton = ttk.Checkbutton(verbose_frame, text="Verbose", variable=self.verbose_var)
        verbose_checkbutton.pack(side=tk.LEFT, padx=5)

        # Buttons
        button_frame = ttk.Frame(master, padding=10)
        button_frame.pack(fill=tk.BOTH)
        transcribe_button = ttk.Button(button_frame, text="Transcribe Audio", command=self.transcribe)
        transcribe_button.pack(side=tk.LEFT, padx=5, pady=10, fill=tk.X, expand=True)
        quit_button = ttk.Button(button_frame, text="Quit", command=master.quit)
        quit_button.pack(side=tk.RIGHT, padx=5, pady=10, fill=tk.X, expand=True)

    def browse(self):
        folder_path = filedialog.askdirectory()
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, folder_path)

    def transcribe(self):
        path = self.path_entry.get()
        file_type = self.file_type_entry.get()
        model = self.model_entry.get()
        #language = self.language_entry.get()
        language = None # set to auto-detect
        verbose = self.verbose_var.get()

        # Call the transcribe function with the appropriate arguments
        result = transcribe(path, file_type, model=model, language=language, verbose=verbose)

        # Show the result in a message box
        tk.messagebox.showinfo("Finished!", result)

if __name__ == "__main__":
#    root = tk.Tk()
    root = ThemedTk(theme="clearlooks")
    root.geometry("300x200")
    app = App(root) 
    root.mainloop()