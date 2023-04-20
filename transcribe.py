import whisper 
import glob, os
#import torch #uncomment if using torch with cuda, below too
import datetime

def transcribe(path, file_type, model=None, language=None, verbose=False):
    '''Implementation of OpenAI's whisper model. Downloads model, transcribes audio files in a folder and returns the text files with transcriptions'''

    try:
        os.mkdir('{}/transcriptions'.format(path))
    except FileExistsError:
        pass
    
    glob_file = glob.glob(path+'/*{}'.format(file_type))

    #if torch.cuda.is_available():
    #    generator = torch.Generator('cuda').manual_seed(42)
    #else:
    #    generator = torch.Generator().manual_seed(42)
        
    print('Using {} model'.format(model))
    print('File type is {}'.format(file_type))    
    print('Language is being detected automatically for each file')
    print('Verbosity is set to {}'.format(verbose))
    print('\nThere are {} {} files in path: {}\n\n'.format(len(glob_file), file_type, path))
    
    print('Loading model...')
    model = whisper.load_model(model)
        
    for idx,file in enumerate(glob_file):
        title = os.path.basename(file).split('.')[0]
        
        print('Transcribing file number number {}: {}'.format(idx+1,title))
        print('Model and file loaded...\nStarting transcription...\n')
        result = model.transcribe(
            file, 
            language=language, 
            verbose=verbose
        )
        start=[]
        end=[]
        text=[]
        for i in range(len(result['segments'])):
            start.append(str(datetime.timedelta(seconds=(result['segments'][i]['start']))))
            end.append(str(datetime.timedelta(seconds=(result['segments'][i]['end']))))
            text.append(result['segments'][i]['text'])
        
        with open("{}/transcriptions/{}.txt".format(path,title), 'w', encoding='utf-8') as file:
            file.write(title)
            file.write('\nIn seconds:')
            for i in range(len(result['segments'])):
                file.writelines('\n[{} --> {}]:{}'.format(start[i], end[i], text[i]))
                
        print('\nFinished file number {}.\n\n\n'.format(idx+1))

    return 'Finished transcription, files can be found in {}/transcriptions'.format(path)    
