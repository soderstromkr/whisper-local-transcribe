import os
import sys
import datetime
import time
import site
from glob import glob

# ---------------------------------------------------------------------------
# CUDA setup — must happen before importing faster_whisper / ctranslate2
# ---------------------------------------------------------------------------
def _setup_cuda_libs():
    """Register NVIDIA pip-package lib dirs so ctranslate2 finds CUDA at runtime.

    pip-installed nvidia-cublas-cu12 / nvidia-cudnn-cu12 place their shared
    libraries inside the site-packages tree.  Neither Windows nor Linux
    automatically search those directories, so we must register them
    explicitly:
      - Windows: os.add_dll_directory() + PATH
      - Linux:   LD_LIBRARY_PATH  (read by the dynamic linker)
    """
    try:
        sp_dirs = site.getsitepackages()
    except AttributeError:
        # virtualenv without site-packages helper
        sp_dirs = [os.path.join(sys.prefix, "lib",
                                "python" + ".".join(map(str, sys.version_info[:2])),
                                "site-packages")]

    for sp in sp_dirs:
        nvidia_root = os.path.join(sp, "nvidia")
        if not os.path.isdir(nvidia_root):
            continue
        for pkg in os.listdir(nvidia_root):
            for sub in ("bin", "lib"):
                d = os.path.join(nvidia_root, pkg, sub)
                if not os.path.isdir(d):
                    continue
                if sys.platform == "win32":
                    os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
                    try:
                        os.add_dll_directory(d)
                    except (OSError, AttributeError):
                        pass
                else:
                    # Linux / macOS — prepend to LD_LIBRARY_PATH
                    ld = os.environ.get("LD_LIBRARY_PATH", "")
                    if d not in ld:
                        os.environ["LD_LIBRARY_PATH"] = d + (":" + ld if ld else "")
                        # Also load via ctypes so already-started process sees it
                        import ctypes
                        try:
                            for so in sorted(os.listdir(d)):
                                if so.endswith(".so") or ".so." in so:
                                    ctypes.cdll.LoadLibrary(os.path.join(d, so))
                        except OSError:
                            pass

_setup_cuda_libs()

from faster_whisper import WhisperModel


SUPPORTED_EXTENSIONS = {
    ".wav", ".mp3", ".m4a", ".flac", ".ogg", ".wma", ".aac",
    ".mp4", ".mkv", ".mov", ".webm", ".avi", ".mpeg", ".mpg",
}


def _detect_device():
    """Return (device, compute_type) for the best available backend."""
    try:
        import ctranslate2
        cuda_types = ctranslate2.get_supported_compute_types("cuda")
        if "float16" in cuda_types:
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


# Get the path
def get_path(path):
    all_items = glob(path + '/*')
    media_files = []
    for item in all_items:
        if not os.path.isfile(item):
            continue
        _, ext = os.path.splitext(item)
        if ext.lower() in SUPPORTED_EXTENSIONS:
            media_files.append(item)
    return sorted(media_files)

# Main function
def transcribe(path, glob_file, model=None, language=None, verbose=False, timestamps=True):
    """
    Transcribes audio files in a specified folder using faster-whisper (CTranslate2).

    Args:
        path (str): Path to the folder containing the audio files.
        glob_file (list): List of audio file paths to transcribe.
        model (str, optional): Name of the Whisper model size to use for transcription.
            Defaults to None, which uses the default model.
        language (str, optional): Language code for transcription. Defaults to None,
            which enables automatic language detection.
        verbose (bool, optional): If True, enables verbose mode with detailed information
            during the transcription process. Defaults to False.

    Returns:
        str: A message indicating the result of the transcription process.

    Raises:
        RuntimeError: If an invalid file is encountered, it will be skipped.

    Notes:
        - The function downloads the specified model if not available locally.
        - The transcribed text files will be saved in a "transcriptions" folder
          within the specified path.
        - Uses CTranslate2 for up to 4x faster inference compared to openai-whisper.
        - FFmpeg is bundled via the PyAV dependency — no separate installation needed.

    """
    SEP = "─" * 46

    # ── Step 1: Detect hardware ──────────────────────────────────────
    device, compute_type = _detect_device()
    print(f"⚙  Device: {device}  |  Compute: {compute_type}")

    # ── Step 2: Load model ───────────────────────────────────────────
    print(f"⏳ Loading model '{model}' — downloading if needed...")
    try:
        whisper_model = WhisperModel(model, device=device, compute_type=compute_type)
    except Exception as exc:
        err = str(exc).lower()
        cuda_runtime_missing = (
            device == "cuda"
            and (
                "libcublas" in err
                or "libcudnn" in err
                or "cuda" in err
                or "cannot be loaded" in err
                or "not found" in err
            )
        )
        if not cuda_runtime_missing:
            raise
        print("⚠  CUDA runtime not available; falling back to CPU (int8).")
        print(f"   Reason: {exc}")
        device, compute_type = "cpu", "int8"
        whisper_model = WhisperModel(model, device=device, compute_type=compute_type)
    print("✅ Model ready!")
    print(SEP)

    # ── Step 3: Transcribe files ─────────────────────────────────────
    total_files = len(glob_file)
    print(f"📂 Found {total_files} supported media file(s) in folder")
    print(SEP)

    if total_files == 0:
        output_text = '⚠  No supported media files found — try another folder.'
        print(output_text)
        print(SEP)
        return output_text

    files_transcripted = []
    file_num = 0
    for file in glob_file:
        title = os.path.basename(file).split('.')[0]
        file_num += 1
        print(f"\n{'─' * 46}")
        print(f"📄 File {file_num}/{total_files}: {title}")
        try:
            t_start = time.time()
            segments, info = whisper_model.transcribe(
                file,
                language=language,
                beam_size=5
            )
            audio_duration = info.duration  # seconds
            # Make folder if missing
            os.makedirs('{}/transcriptions'.format(path), exist_ok=True)
            # Stream segments as they are decoded
            segment_list = []
            with open("{}/transcriptions/{}.txt".format(path, title), 'w', encoding='utf-8') as f:
                f.write(title)
                f.write('\n' + '─' * 40 + '\n')
                for seg in segments:
                    text = seg.text.strip()
                    if timestamps:
                        start_ts = str(datetime.timedelta(seconds=seg.start))
                        end_ts = str(datetime.timedelta(seconds=seg.end))
                        f.write('\n[{} --> {}] {}'.format(start_ts, end_ts, text))
                    else:
                        f.write('\n{}'.format(text))
                    f.flush()
                    if verbose:
                        print("   [%.2fs → %.2fs] %s" % (seg.start, seg.end, seg.text))
                    else:
                        print("   Transcribed up to %.0fs..." % seg.end, end='\r')
                    segment_list.append(seg)
            elapsed = time.time() - t_start
            elapsed_min = elapsed / 60.0
            audio_min = audio_duration / 60.0
            ratio = audio_duration / elapsed if elapsed > 0 else float('inf')
            print(f"✅ Done — saved to transcriptions/{title}.txt")
            print(f"⏱  Transcribed {audio_min:.1f} min of audio in {elapsed_min:.1f} min  ({ratio:.1f}x realtime)")
            files_transcripted.append(segment_list)
        except Exception as exc:
            print(f"⚠  Could not decode '{os.path.basename(file)}', skipping.")
            print(f"   Reason: {exc}")

    # ── Summary ──────────────────────────────────────────────────────
    print(f"\n{SEP}")
    if len(files_transcripted) > 0:
        output_text = f"✅ Finished! {len(files_transcripted)} file(s) transcribed.\n   Saved in: {path}/transcriptions"
    else:
        output_text = '⚠  No files eligible for transcription — try another folder.'
    print(output_text)
    print(SEP)
    return output_text
