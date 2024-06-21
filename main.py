import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import os
import asyncio
import edge_tts
from whisper_cpp_python import Whisper
from whisper_cpp_python.whisper_cpp import whisper_progress_callback
import random
import string

app = FastAPI()

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

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def generate_unique_filename():
    """Generates a unique random string of 10 characters."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def get_text(file_path):
    output = model.transcribe(file_path)
    output_text = output.get('text')
    return output_text

async def convert_to_speech(text, filename, voice=0):
    TEXT = text
    VOICES = ['en-US-GuyNeural', 'en-US-JennyNeural', 'en-GB-SoniaNeural']
    VOICE = VOICES[voice]
    OUTPUT_FILE = filename

    print("converting to mp3")
    communicate = edge_tts.Communicate(TEXT, VOICE, rate="-10%")
    await communicate.save(OUTPUT_FILE)
    print("Task complete")
    return OUTPUT_FILE

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")
    
    filename = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    print(f'File saved as {filename}')
    
    text = get_text(filename)
    print("Text: ", text)

    unique_filename = generate_unique_filename()
    output_filename = os.path.join(UPLOAD_FOLDER, f"{unique_filename}.mp3")
    
    await convert_to_speech(text, output_filename)
    
    return FileResponse(output_filename, media_type="audio/mpeg", filename=f"{unique_filename}.mp3")

@app.get("/")
async def home():
    return {"message": "Hello, World!"}
