import json
import os
import requests
from django.conf import settings
from channels.generic.websocket import WebsocketConsumer
from google.cloud import speech
from io import BytesIO
import base64
from pydub import AudioSegment

# Define the Perspective API URL
PERSPECTIVE_API_URL = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"

# Helper function to call the Perspective API for toxicity analysis
def analyze_toxicity(text):
    data = {
        "comment": {"text": text},
        "languages": ["en"],
        "requestedAttributes": {"TOXICITY": {}}
    }
    
    # Send a POST request to the Perspective API
    response = requests.post(
        PERSPECTIVE_API_URL,
        params={"key": settings.GOOGLE_API_KEY},  # Your API key from settings
        json=data
    )
    
    # Parse and return the API response in JSON format
    return response.json()

# Helper function to call Google Speech-to-Text API and convert speech to text
def transcribe_audio(audio_data):
    client = speech.SpeechClient()  # Create a Speech client instance
    
    # Prepare the audio data for Google Speech-to-Text API
    audio = speech.RecognitionAudio(content=audio_data)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )
    
    # Perform the speech-to-text operation
    response = client.recognize(config=config, audio=audio)
    
    # Extract and return the transcript (first result)
    if response.results:
        transcript = response.results[0].alternatives[0].transcript
        return transcript
    return None

# Define the WebSocket consumer for handling both text and audio messages
class ChatConsumer(WebsocketConsumer):
    
    def connect(self):
        self.accept()  # Accept the WebSocket connection

    def receive(self, text_data):
        text_data_json = json.loads(text_data)  # Parse the received JSON data

        # Check if the message contains text or audio
        if 'message' in text_data_json:
            # Process text message
            message = text_data_json['message']
            self.handle_text_message(message)
        
        elif 'audio' in text_data_json:
            # Process audio message (base64-encoded)
            audio_data_base64 = text_data_json['audio']
            self.handle_audio_message(audio_data_base64)

    def handle_text_message(self, message):
        """Handle and analyze the text message for toxicity."""
        # Call the Perspective API to analyze toxicity
        result = analyze_toxicity(message)
        
        # Extract the toxicity score from the API response
        toxicity_score = result['attributeScores']['TOXICITY']['summaryScore']['value']
        is_toxic = toxicity_score >= 0.5  # Define a threshold for toxicity (50%)

        # Send the result back to the client
        self.send(text_data=json.dumps({
            'message': message,
            'toxicity_level': f"{toxicity_score * 100:.2f}%",  # Convert to percentage
            'is_toxic': is_toxic
        }))

    def handle_audio_message(self, audio_data_base64):
        """Handle audio message, convert it to text and analyze for toxicity."""
        # Decode the base64 audio data
        audio_data = base64.b64decode(audio_data_base64)
        
        # Convert the audio to WAV format using pydub
        audio_segment = AudioSegment.from_file(BytesIO(audio_data), format="webm")
        wav_audio = BytesIO()
        audio_segment.export(wav_audio, format="wav")
        wav_audio.seek(0)  # Move to the beginning of the audio stream

        # Call Google Speech-to-Text API to transcribe the audio
        transcript = transcribe_audio(wav_audio.read())

        if transcript:
            # Analyze the transcript for toxicity
            self.handle_text_message(transcript)
        else:
            # If transcription fails, send an error message
            self.send(text_data=json.dumps({
                'error': 'Failed to transcribe the audio message.'
            }))
