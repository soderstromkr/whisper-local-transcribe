## transcribe
Simple implementation of OpenAI's Whisper to transcribe audio files from your local folders. 

### Instructions 
#### Requirements
1. This script was made and tested in an Anaconda environment with python 3.10, if you're not familiar with python I would recommend this method. 
See [here](https://docs.anaconda.com/anaconda/install/index.html) for instructions. You might need administrator rights. 
2. Whisper requires some additional libraries. The [setup](https://github.com/openai/whisper#setup) page states: "The codebase also depends on a few Python packages, most notably HuggingFace Transformers for their fast tokenizer implementation and ffmpeg-python for reading audio files."
Users might not need to specifically install Transfomers. However, a conda installation might be needed for ffmepg, which takes care of setting up PATH variables. Install with:
```
 conda install -c conda-forge ffmpeg-python
 ```
Advanced users can use ```pip install ffmpeg-python``` but be ready to deal with some [PATH issues](https://stackoverflow.com/questions/65836756/python-ffmpeg-wont-accept-path-why), which I encountered in Windows 11.
 3. The main functionality comes from openai-whisper. See their [page](https://github.com/openai/whisper) for details. As of 2023-03-22 you can install via:
```
pip install -U openai-whisper
```
#### Using the script
This is a simple script with no installation. You can either clone the repository with
```
git clone https://github.com/soderstromkr/transcribe.git
```
and use the example.ipynb template to use the script **OR** download the ```transcribe.py``` file into your work folder. Then you can either import it to another script or notebook for use. I recommend jupyter notebook for new users.

### Example
See the [example](example.ipynb) implementation on jupyter notebook.


