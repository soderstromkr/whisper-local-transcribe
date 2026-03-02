### How to run on Mac / Linux

#### Quick start
1. Open Terminal and navigate to the project folder (or right-click the folder and select "Open in Terminal").
2. Make the script executable (only needed once):
```
chmod +x run_Mac.sh
```
3. Run it:
```
./run_Mac.sh
```

This will automatically:
- Create a virtual environment (`.venv`)
- Install all dependencies (no admin rights needed)
- Launch the app

#### Manual steps (alternative)
If you prefer to do it manually:
```
python3 -m venv .venv
.venv/bin/python install.py
.venv/bin/python app.py
```

#### Notes
- **Python 3.10+** is required. macOS users can install it from [python.org](https://www.python.org/downloads/) or via `brew install python`.
- **No FFmpeg install needed** — audio decoding is bundled.
- **GPU acceleration** is not available on macOS (Apple Silicon MPS is not supported by CTranslate2). CPU with int8 quantization is still fast.
- On Apple Silicon (M1/M2/M3/M4), the `small` or `base` models run well. `medium` works but is slower.
