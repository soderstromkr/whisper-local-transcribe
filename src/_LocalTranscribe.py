import os
import sys
import datetime
import site
from glob import glob

# ---------------------------------------------------------------------------
# CUDA setup — must happen before importing faster_whisper / ctranslate2
# ---------------------------------------------------------------------------
def _setup_cuda_dlls():
    """Add NVIDIA pip-package DLL dirs to the DLL search path (Windows only).

    pip-installed nvidia-cublas-cu12 / nvidia-cudnn-cu12 place their .dll
    files inside the site-packages tree.  Python 3.8+ on Windows does NOT
    search PATH for DLLs loaded via ctypes/LoadLibrary, so we must
    explicitly register every nvidia/*/bin and nvidia/*/lib directory using
    os.add_dll_directory *and* prepend them to PATH (some native extensions
    still rely on PATH).
    """
    if sys.platform != "win32":
        return
    try:
        for sp in site.getsitepackages():
            nvidia_root = os.path.join(sp, "nvidia")
            if not os.path.isdir(nvidia_root):
                continue
            for pkg in os.listdir(nvidia_root):
                for sub in ("bin", "lib"):
                    d = os.path.join(nvidia_root, pkg, sub)
                    if os.path.isdir(d):
                        os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
                        try:
                            os.add_dll_directory(d)
                        except (OSError, AttributeError):
                            pass
    except Exception:
        pass

_setup_cuda_dlls()

from faster_whisper import WhisperModel


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
    glob_file = glob(path + '/*')
    return glob_file

# Main function
def transcribe(path, glob_file, model=None, language=None, verbose=False):
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
    whisper_model = WhisperModel(model, device=device, compute_type=compute_type)
    print("✅ Model ready!")
    print(SEP)

    # ── Step 3: Transcribe files ─────────────────────────────────────
    total_files = len(glob_file)
    print(f"📂 Found {total_files} item(s) in folder")
    print(SEP)

    files_transcripted = []
    file_num = 0
    for file in glob_file:
        title = os.path.basename(file).split('.')[0]
        file_num += 1
        print(f"\n{'─' * 46}")
        print(f"📄 File {file_num}/{total_files}: {title}")
        try:
            segments, info = whisper_model.transcribe(
                file,
                language=language,
                beam_size=5
            )
            # Make folder if missing
            os.makedirs('{}/transcriptions'.format(path), exist_ok=True)
            # Stream segments as they are decoded
            segment_list = []
            with open("{}/transcriptions/{}.txt".format(path, title), 'w', encoding='utf-8') as f:
                f.write(title)
                for seg in segments:
                    start_ts = str(datetime.timedelta(seconds=seg.start))
                    end_ts = str(datetime.timedelta(seconds=seg.end))
                    f.write('\n[{} --> {}]:{}'.format(start_ts, end_ts, seg.text))
                    f.flush()
                    if verbose:
                        print("   [%.2fs → %.2fs] %s" % (seg.start, seg.end, seg.text))
                    else:
                        print("   Transcribed up to %.0fs..." % seg.end, end='\r')
                    segment_list.append(seg)
            print(f"✅ Done — saved to transcriptions/{title}.txt")
            files_transcripted.append(segment_list)
        except Exception:
            print('⚠  Not a valid audio/video file, skipping.')

    # ── Summary ──────────────────────────────────────────────────────
    print(f"\n{SEP}")
    if len(files_transcripted) > 0:
        output_text = f"✅ Finished! {len(files_transcripted)} file(s) transcribed.\n   Saved in: {path}/transcriptions"
    else:
        output_text = '⚠  No files eligible for transcription — try another folder.'
    print(output_text)
    print(SEP)
    return output_text
