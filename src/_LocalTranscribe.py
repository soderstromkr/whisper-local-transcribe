import os
import datetime
from glob import glob
import whisper
from torch import backends, cuda, Generator
import colorama
from colorama import Back,Fore
colorama.init(autoreset=True)


# Get the path
def get_path(path):
    glob_file = glob(path + '/*')
    return glob_file

# Main function
def transcribe(path, glob_file, model=None, language=None, verbose=False):
    """
    Transcribes audio files in a specified folder using OpenAI's Whisper model.

    Args:
        path (str): Path to the folder containing the audio files.
        glob_file (list): List of audio file paths to transcribe.
        model (str, optional): Name of the Whisper model to use for transcription.
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

    """
    # Check for GPU acceleration
    if backends.mps.is_available():
        Generator('mps').manual_seed(42)
    elif cuda.is_available():
        Generator('cuda').manual_seed(42)
    else:
        Generator().manual_seed(42)

    # Load model
    model = whisper.load_model(model)
    # Start main loop
    files_transcripted=[]   
    for file in glob_file:
        title = os.path.basename(file).split('.')[0]
        print(Back.CYAN + '\nTrying to transcribe file named: {}\U0001f550'.format(title))
        try:
            result = model.transcribe(
                file, 
                language=language, 
                verbose=verbose
                )
            files_transcripted.append(result)
            # Make folder if missing 
            try:
                os.makedirs('{}/transcriptions'.format(path), exist_ok=True)
            except FileExistsError:
                pass
            # Create segments for text files
            start = []
            end = []
            text = []
            for segment in result['segments']:
                start.append(str(datetime.timedelta(seconds=segment['start'])))
                end.append(str(datetime.timedelta(seconds=segment['end'])))
                text.append(segment['text'])
            # Save files to transcriptions folder
            with open("{}/transcriptions/{}.txt".format(path, title), 'w', encoding='utf-8') as file:
                file.write(title)
                for i in range(len(result['segments'])):
                    file.write('\n[{} --> {}]:{}'.format(start[i], end[i], text[i]))
        # Skip invalid files
        except RuntimeError:
            print(Fore.RED + 'Not a valid file, skipping.')
            pass
     # Check if any files were processed.
    if len(files_transcripted) > 0:
        output_text = 'Finished transcription, {} files can be found in {}/transcriptions'.format(len(files_transcripted), path)
    else:
        output_text = 'No files elligible for transcription, try adding audio or video files to this folder or choose another folder!'
    # Return output text
    return output_text
