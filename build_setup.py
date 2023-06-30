from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ['whisper','tkinter','customtkinter']
    }
executables = (
    [
        Executable(
            "app.py",
            icon='images/icon.ico',
        )
    ]
)
setup(
    name="Local Transcribe with Whisper",
    version="1.2",
    author="Kristofer Rolf Söderström",
    options={"build_exe":build_exe_options},
    executables=executables
)