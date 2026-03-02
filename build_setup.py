from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ['faster_whisper','tkinter','customtkinter']
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
    version="2.0",
    author="Kristofer Rolf Söderström",
    options={"build_exe":build_exe_options},
    executables=executables
)