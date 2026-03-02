#!/bin/bash
# ============================================================
#  Local Transcribe with Whisper — macOS / Linux launcher
# ============================================================
# Double-click this file or run:  ./run_Mac.sh
# On first run it creates a venv and installs dependencies.
# ============================================================

set -e

cd "$(dirname "$0")"

# Create .venv if it doesn't exist
if [ ! -f ".venv/bin/python" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

PYTHON=".venv/bin/python"

# Install dependencies on first run
if ! "$PYTHON" -c "import faster_whisper" 2>/dev/null; then
    echo "First run detected — running installer..."
    "$PYTHON" install.py
    echo
fi

echo "Starting Local Transcribe..."
"$PYTHON" app.py
