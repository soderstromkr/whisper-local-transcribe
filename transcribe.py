import whisper 
import glob, os

def transcribe(path, file_type, model='base', language=None, verbose=True):
  '''Implementation of OpenAI's whisper model. Downloads model, transcribes audio files
  in a folder and returns the text files with transcriptions.'''
    
    try:
        os.mkdir('{}transcriptions'.format(path))
    except FileExistsError:
        pass
    
    glob_file = glob.glob(path+'/*{}'.format(file_type))
    path = path
    
    print('Using {} model, you can change this by specifying model="medium" for example'.format(model))
    print('Only looking for file type {}, you can change this by specifying file_type="mp3"'.format(file_type))    
    print('Expecting {} language, you can change this by specifying language="English". None will try to auto-detect'.format(language))
    print('Verbosity is {}. If TRUE it will print out the text as it is transcribed, you can turn this off by setting verbose=False'.format(verbose))
    print('\nThere are {} {} files in path: {}\n\n'.format(len(glob_file), file_type, path))
    print('Loading model...')
    model = whisper.load_model(model)
    
    
    
    for idx,file in enumerate(glob_file):
        title = os.path.basename(file).split('.')[0]
        
        print('Transcribing file number number {}: {}'.format(idx+1,file))
        print('Model and file loaded...\nStarting transcription...\n')
        result = model.transcribe(
            file, 
            language=language, 
            verbose=True
        )
        start=[]
        end=[]
        text=[]
        for i in range(len(result['segments'])):
            start.append(result['segments'][i]['start'])
            end.append(result['segments'][i]['end'])
            text.append(result['segments'][i]['text'])
        
        with open("{}transcriptions/{}.txt".format(path,title), 'w', encoding='utf-8') as file:
            file.write(title)
            file.write('\nIn seconds:')
            for i in range(len(result['segments'])):
                file.writelines('\n[{:.2f} --> {:.2f}]:{}'.format(start[i], end[i], text[i]))
                
        print('\nFinished file number {}.\n\n\n'.format(idx+1))

    return 'Finished transcription, files can be found in {}'.format(path)    
