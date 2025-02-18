import os
import datetime
from glob import glob
import whisper
from torch import cuda, Generator
import colorama
from colorama import Back, Fore
colorama.init(autoreset=True)

def get_path(path):
    return glob(path + '/*')

def transcribe(path, glob_file, model=None, language=None, verbose=False, max_segment_duration=None, srt_format=False, min_segment_duration=0):
    device = "cuda" if cuda.is_available() else "cpu"
    print(f"Using {device.upper()} for transcription")

    model = whisper.load_model(model).to(device)
    files_transcripted = []

    for file in glob_file:
        title = os.path.basename(file).split('.')[0]
        print(Back.CYAN + f'\nTrying to transcribe file named: {title}\U0001f550')

        try:
            transcribe_kwargs = {
                'language': language,
                'verbose': verbose,
                'word_timestamps': max_segment_duration is not None,
                'fp16': cuda.is_available()
            }

            result = model.transcribe(file, **transcribe_kwargs)
            files_transcripted.append(result)
            os.makedirs(f'{path}/transcriptions', exist_ok=True)

            segments = []            
            for segment in result['segments']:
                if max_segment_duration:
                    # Pass both max and min durations to the splitting function
                    segments += split_segment(segment, max_segment_duration, min_duration=min_segment_duration)
                else:
                    segments.append({
                        'start': segment['start'],
                        'end': segment['end'],
                        'text': segment['text']
                    })

            with open(f"{path}/transcriptions/{title}.{'srt' if srt_format else 'txt'}", 'w', encoding='utf-8') as f:
                if srt_format:
                    for i, seg in enumerate(segments, start=1):
                        f.write(f"{i}\n")
                        f.write(f"{format_timedelta_srt(seg['start'])} --> {format_timedelta_srt(seg['end'])}\n")
                        f.write(f"{seg['text'].strip()}\n\n")
                else:
                    f.write(title)
                    for seg in segments:
                        start = str(datetime.timedelta(seconds=seg['start'])).split('.')[0]
                        end = str(datetime.timedelta(seconds=seg['end'])).split('.')[0]
                        f.write(f"\n[{start} --> {end}]: {seg['text']}")

        except RuntimeError:
            print(Fore.RED + 'Not a valid file, skipping.')
            continue

    return f'Finished transcription, {len(files_transcripted)} files in {path}/transcriptions'

def split_segment(segment, max_duration, min_duration=0):
    # If the entire segment is already short, return it as is.
    if segment['end'] - segment['start'] <= max_duration:
        return [segment]
    
    chunks = []
    words = segment.get('words', [])
    
    # If word timestamps are not available, use the fallback.
    if not words:
        return duration_split(segment, max_duration)
    
    current_start = segment['start']
    current_text = []
    
    for word in words:
        # If adding this word would exceed max_duration and we have some text accumulated...
        if (word['end'] - current_start) > max_duration and current_text:
            chunks.append({
                'start': current_start,
                'end': word['start'],  # you might choose to use previous word's end if desired
                'text': ' '.join(current_text)
            })
            current_start = word['start']
            current_text = [word['text'].strip()]
        else:
            current_text.append(word['text'].strip())
    
    # Add any remaining words as a chunk.
    if current_text:
        chunks.append({
            'start': current_start,
            'end': words[-1]['end'],
            'text': ' '.join(current_text)
        })
    
    # Optionally, merge chunks that are too short
    if min_duration > 0:
        chunks = merge_short_chunks(chunks, min_duration)
    
    return chunks

def merge_short_chunks(chunks, min_duration):
    if not chunks:
        return chunks
    merged = [chunks[0]]
    for chunk in chunks[1:]:
        prev_chunk = merged[-1]
        # If the duration of the previous chunk is less than min_duration, merge it with the current chunk.
        if (prev_chunk['end'] - prev_chunk['start']) < min_duration:
            merged[-1] = {
                'start': prev_chunk['start'],
                'end': chunk['end'],
                'text': prev_chunk['text'] + ' ' + chunk['text']
            }
        else:
            merged.append(chunk)
    return merged

def duration_split(segment, max_duration):
    """Fallback splitting when word timestamps are unavailable"""
    chunks = []
    start = segment['start']
    end = segment['end']
    duration = end - start
    
    if duration <= max_duration:
        return [segment]
    
    num_splits = int(duration // max_duration) + 1
    chunk_duration = duration / num_splits
    
    for i in range(num_splits):
        chunk_start = start + i * chunk_duration
        chunk_end = min(start + (i+1) * chunk_duration, end)
        chunks.append({
            'start': chunk_start,
            'end': chunk_end,
            'text': segment['text'][i*len(segment['text'])//num_splits : (i+1)*len(segment['text'])//num_splits]
        })
    
    return chunks

def format_timedelta_srt(seconds):
    """Directly convert seconds to SRT format"""
    td = datetime.timedelta(seconds=seconds)
    total_seconds = td.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds - int(total_seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
