## transcribe
Simple implementation of OpenAI's Whisper to transcribe audio files from your local folders. 

### Instructions 
#### Using the script
1. This package was made and tested in an Anaconda environment, if you're not familiar with python I would recommend this method. 
See [here](https://docs.anaconda.com/anaconda/install/index.html) for instructions.
2. This is a simple script with no installation. Simply download the .py file into your work folder. Then you can either import it to another script or notebook for use. I recommend jupyter notebook for new users.
#### Requirements
1. Whisper requires some additional libraries. The [setup](https://github.com/openai/whisper#setup) page states: "The codebase also depends on a few Python packages, most notably HuggingFace Transformers for their fast tokenizer implementation and ffmpeg-python for reading audio files."
Users might not need to specifically install Transfomers. However, a conda installation might be needed for ffmepg, which takes care of setting up PATH variables. Install with:
```
 conda install -c conda-forge ffmpeg-python
 ```
3. The main functionality comes from openai-whisper. See their [page](https://github.com/openai/whisper) for details. As of 2023-03-22 you can install via:
```
pip install -U openai-whisper
```
### Example
See the [example](example.ipynb) implementation on jupyter notebook.
