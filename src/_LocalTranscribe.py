import os
import datetime
from glob import glob
import whisper
from torch import cuda, Generator
import colorama
from colorama import Back,Fore
colorama.init(autoreset=True)

def get_path(path):
    return glob(path + '/*')

def transcribe(path, glob_file, model=None, language=None, verbose=False, max_segment_duration=None, srt_format=False):
    if cuda.is_available():
        Generator('cuda').manual_seed(42)
    else:
        Generator().manual_seed(42)
        
    device = "cuda" if cuda.is_available() else "cpu"
    print(f"Using {device.upper()} for transcription")

        
    model = whisper.load_model(model).to(device)
    files_transcripted = []
    
    for file in glob_file:
        title = os.path.basename(file).split('.')[0]
        print(Back.CYAN + '\nTrying to transcribe file named: {}\U0001f550'.format(title))
        
        try:
            # Enable word timestamps if duration control is needed
            transcribe_kwargs = {
                'language': language,
                'verbose': verbose,
                'word_timestamps': max_segment_duration is not None,
                'fp16': cuda.is_available()  # This enables FP16 when using GPU
            }

            result = model.transcribe(file, **transcribe_kwargs)
            
            files_transcripted.append(result)
            os.makedirs(f'{path}/transcriptions', exist_ok=True)
            
            start, end, text = [], [], []
            for segment in result['segments']:
                if max_segment_duration:
                    process_segment_with_duration(segment, max_segment_duration, start, end, text)
                else:
                    start.append(str(datetime.timedelta(seconds=segment['start'])))
                    end.append(str(datetime.timedelta(seconds=segment['end'])))
                    text.append(segment['text'])
            
            with open(f"{path}/transcriptions/{title}.{'srt' if srt_format else 'txt'}", 'w', encoding='utf-8') as f:
                if srt_format:
                    for i, (s, e, t) in enumerate(zip(start, end, text), start=1):
                        # Directly use original float values instead of string parsing
                        start_sec = float(s.split(':')[-1]) if isinstance(s, str) else s
                        end_sec = float(e.split(':')[-1]) if isinstance(e, str) else e
                        
                        f.write(f"{i}\n")
                        f.write(f"{format_timedelta_srt(datetime.timedelta(seconds=start_sec))} --> "
                                f"{format_timedelta_srt(datetime.timedelta(seconds=end_sec))}\n")
                        f.write(f"{t}\n\n")
                else:
                    f.write(title)
                    for s, e, t in zip(start, end, text):
                        f.write(f'\n[{s} --> {e}]: {t}')

                    
        except RuntimeError:
            print(Fore.RED + 'Not a valid file, skipping.')
            continue

    return f'Finished transcription, {len(files_transcripted)} files in {path}/transcriptions'

def process_segment_with_duration(segment, max_duration, start_list, end_list, text_list):
    words = segment.get('text', [])
    if not words:
        start_list.append(str(datetime.timedelta(seconds=segment['start'])))
        end_list.append(str(datetime.timedelta(seconds=segment['end'])))
        text_list.append(segment['text'])
        return

    current_start = None
    current_text = []
    for word in words:
        # Handle cases where word dict might not have 'text' key
        if 'text' not in word:
            continue  # Skip words without text
            
        word_text = word['text'].strip()
        if not word_text:  # Skip empty text entries
            continue
            
        word_start = word.get('start')
        word_end = word.get('end')

        # Skip words missing timestamps
        if word_start is None or word_end is None:
            continue

        if current_start is None:
            current_start = word_start
            current_end = word_end
            current_text = [word_text]
        else:
            if (word_end - current_start) <= max_duration:
                current_end = word_end
                current_text.append(word_text)
            else:
                start_list.append(str(datetime.timedelta(seconds=current_start)).split('.')[0])
                end_list.append(str(datetime.timedelta(seconds=current_end)))
                text_list.append(' '.join(current_text))
                current_start = word_start
                current_end = word_end
                current_text = [word_text]

    if current_start is not None and current_text:
        start_list.append(str(datetime.timedelta(seconds=current_start)).split('.')[0])
        end_list.append(str(datetime.timedelta(seconds=current_end)))
        text_list.append(' '.join(current_text))

def format_timedelta_srt(td):
    """Convert timedelta to SRT format HH:MM:SS,mmm"""
    total_seconds = td.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds - int(total_seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
