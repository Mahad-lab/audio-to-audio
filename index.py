from flask import Flask, request, send_file
import os
import asyncio
import edge_tts
from whisper_cpp_python import Whisper
from whisper_cpp_python.whisper_cpp import whisper_progress_callback

import random
import string


# Define the local path where the file should be saved
model_file_path = "ggml-model-whisper-tiny.bin"

# Check if the file exists locally
if not os.path.exists(model_file_path):
    import requests
    # Define the URL of the file to download
    url = "https://ggml.ggerganov.com/ggml-model-whisper-tiny.bin"
    
    # Send a request to the URL
    response = requests.get(url)
    
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Open the local file in write mode and write the content of the response
        with open(model_file_path, 'wb') as file:
            file.write(response.content)
        print(f"File downloaded successfully.")
    else:
        print("Failed to download the file.")
else:
    print("File already exists locally.")


def callback(ctx, state, i, p):
    print(i)

model = Whisper(model_file_path)
model.params.progress_callback = whisper_progress_callback(callback)
print("Model loaded successfully.")

def generate_unique_filename():
  """Generates a unique random string of 10 characters."""
  return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def get_text(file):
    output = model.transcribe(file)
    output_text = output.get('text')
    return output_text

def convert_to_speech(text, filename, voice=0):
    TEXT = text
    VOICES = [ 'en-US-GuyNeural', 'en-US-JennyNeural', 'en-GB-SoniaNeural']
    VOICE = VOICES[voice]
    OUTPUT_FILE = filename

    async def amain() -> None:
        """Main function"""
        print("converting to mp3")
        communicate = edge_tts.Communicate(TEXT, VOICE, rate="-10%")
        await communicate.save(OUTPUT_FILE)

    print("getting loop")
    # Get the current event loop
    loop = asyncio.get_event_loop()

    print("Running task")
    # Create a task for the coroutine and schedule it
    task = loop.create_task(amain())

    print("Waiting for task to complete")
    try:
        print("Running loop")
        loop.run_until_complete(task)
        print("loop complete")
    finally:
        print("Closing loop")
        try:
            loop.close()
        except:
            print("Loop already closed")
        
    print("Task complete")
    return OUTPUT_FILE

app = Flask(__name__)
print("Flask app created")

# Configure maximum content length to 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Directory where the uploaded files will be saved
UPLOAD_FOLDER = 'uploads'

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

print("Upload folder created")

@app.route('/')
def home():
    return 'Hello, World!'


@app.route('/upload', methods=['POST'])
def upload_file():
    print('/upload')
    if 'file' not in request.files:
        return 'No file part', 400
    print('file found')
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    print('file selected')
    if file:
        # Save the file to the UPLOAD_FOLDER
        filename = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filename)
        print(f'File saved as {filename}')
        
        # Here you would add your file processing logic
        text = get_text(filename)
        print("Text: ", text)

        unique_filename = generate_unique_filename()
        output_filename = os.path.join(UPLOAD_FOLDER, f"{unique_filename}.mp3")

        # random characters
        convert_to_speech(text, output_filename)
        
        # Send the processed file back to the client
        return send_file(output_filename, as_attachment=True)


@app.route('/about')
def about():
    return 'About'