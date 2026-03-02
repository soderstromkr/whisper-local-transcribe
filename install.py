"""
Installer script for Local Transcribe with Whisper.
Detects NVIDIA GPU and offers to install GPU acceleration support.

Usage:
    python install.py
"""

import os
import subprocess
import sys
import shutil
import site


def detect_nvidia_gpu():
    """Check if an NVIDIA GPU is present."""
    candidates = [
        shutil.which("nvidia-smi"),
        r"C:\Windows\System32\nvidia-smi.exe",
        r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe",
    ]
    for path in candidates:
        if not path or not os.path.isfile(path):
            continue
        try:
            r = subprocess.run(
                [path, "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip():
                return True, r.stdout.strip().split("\n")[0]
        except Exception:
            continue
    return False, None


def pip_install(*packages):
    cmd = [sys.executable, "-m", "pip", "install"] + list(packages)
    print(f"\n> {' '.join(cmd)}\n")
    subprocess.check_call(cmd)


def get_site_packages():
    for p in site.getsitepackages():
        if p.endswith("site-packages"):
            return p
    return site.getsitepackages()[0]


def create_nvidia_pth():
    """Create a .pth startup hook that registers NVIDIA DLL directories."""
    sp = get_site_packages()
    pth_path = os.path.join(sp, "nvidia_cuda_path.pth")
    # This one-liner runs at Python startup, before any user code.
    pth_content = (
        "import os, glob as g; "
        "any(os.add_dll_directory(d) or os.environ.__setitem__('PATH', d + os.pathsep + os.environ.get('PATH','')) "
        "for d in g.glob(os.path.join(r'" + sp.replace("'", "\\'") + "', 'nvidia', '*', 'bin')) "
        "+ g.glob(os.path.join(r'" + sp.replace("'", "\\'") + "', 'nvidia', '*', 'lib')) "
        "if os.path.isdir(d)) if os.name == 'nt' else None\n"
    )
    with open(pth_path, "w") as f:
        f.write(pth_content)
    print(f"  Created CUDA startup hook: {pth_path}")


def verify_cuda():
    """Verify CUDA works in a fresh subprocess."""
    try:
        r = subprocess.run(
            [sys.executable, "-c",
             "import ctranslate2; "
             "print('float16' in ctranslate2.get_supported_compute_types('cuda'))"],
            capture_output=True, text=True, timeout=30,
        )
        return r.stdout.strip() == "True"
    except Exception:
        return False


def main():
    print("=" * 55)
    print("  Local Transcribe with Whisper — Installer")
    print("=" * 55)

    # Step 1: Base packages
    print("\n[1/2] Installing base requirements...")
    pip_install("-r", "requirements.txt")
    print("\n  Base requirements installed!")

    # Step 2: GPU
    print("\n[2/2] Checking for NVIDIA GPU...")
    has_gpu, gpu_name = detect_nvidia_gpu()

    if has_gpu:
        print(f"\n  NVIDIA GPU detected: {gpu_name}")
        print("  GPU acceleration can make transcription 2-5x faster.")
        print("  This will install ~300 MB of additional CUDA libraries.\n")

        while True:
            answer = input("  Install GPU support? [Y/n]: ").strip().lower()
            if answer in ("", "y", "yes"):
                print("\n  Installing CUDA libraries...")
                pip_install("nvidia-cublas-cu12", "nvidia-cudnn-cu12")
                create_nvidia_pth()
                print("\n  Verifying CUDA...")
                if verify_cuda():
                    print("  GPU support verified and working!")
                else:
                    print("  WARNING: CUDA installed but not detected.")
                    print("  Update your NVIDIA drivers and try again.")
                break
            elif answer in ("n", "no"):
                print("\n  Skipping GPU. Re-run install.py to add it later.")
                break
            else:
                print("  Please enter Y or N.")
    else:
        print("\n  No NVIDIA GPU detected — using CPU mode.")

    print("\n" + "=" * 55)
    print("  Done! Run the app with:  python app.py")
    print("=" * 55)


if __name__ == "__main__":
    main()
