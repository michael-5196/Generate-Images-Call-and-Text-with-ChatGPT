import google
import os
import openai
import base64
import requests
import string
import tempfile
import shutil
import textwrap
from google.cloud import texttospeech, speech_v1
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from flask import Flask, request, send_from_directory, url_for
from google.api_core.exceptions import GoogleAPICallError
from google.oauth2 import service_account
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Set up the OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Set up the Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\youractual\filepath\keyfile.json"

# Set up the Twilio credentials
os.environ["TWILIO_ACCOUNT_SID"] = os.environ.get("TWILIO_ACCOUNT_SID")
os.environ["TWILIO_AUTH_TOKEN"] = os.environ.get("TWILIO_AUTH_TOKEN")
os.environ["TWILIO_NUMBER"] = os.environ.get("TWILIO_NUMBER")

# Set up the Google Cloud Speech-to-Text client
speech_client = speech_v1.SpeechClient()

# Get the Twilio credentials
twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
twilio_from_number = os.environ.get("TWILIO_NUMBER")

twilio_client = Client(twilio_account_sid, twilio_auth_token)

# Define the conversation history and turn count globally
conversation_history = []
turn_count = 0

# Generate an image based on a text prompt
def generate_image(prompt):
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    image_url = response['data'][0]['url']
    return image_url




def synthesize_text_to_speech(text):
    # Create a Text-to-Speech client
    client = texttospeech.TextToSpeechClient()

    # Set up the input text
    input_text = texttospeech.SynthesisInput(text=text)

    # Set up the voice parameters
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", name="en-US-Neural2-D"
    )

    # Set up the audio configuration
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request
    try:
        response = client.synthesize_speech(
            input=input_text, voice=voice, audio_config=audio_config
        )
        # Return the audio content
        return response.audio_content
    except Exception as e:
        print(f"Error synthesizing speech: {e}")
        # Return an empty bytes object instead of a string
        return b""


@app.route("/sms", methods=["POST"])
def sms_reply():
    """Respond to incoming text messages with a message from your bot."""
    # Get the message the user sent our Twilio number
    body = request.values.get('Body', None)

    # Start our TwiML response
    resp = MessagingResponse()

    # Check if the user requested an image
    if body.lower().startswith('img'):
        try:
            # Get the prompt for the image from the user's message
            prompt = body[4:]  # Get the rest of the message after 'img'

            # Generate the image using OpenAI
            image_url = generate_image(prompt)

            # Attach the image URL to the response
            resp.message("Here is your image:").media(image_url)

        except Exception as e:
            print(f"Error: {e}")
            resp.message("Sorry, I couldn't generate your image.")
    else:
        # Add the user's message to the conversation history
        conversation_history.append(f"User: {body}")

        # Generate a response
        try:
            openai_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": body},
                ]
            )

            ai_response = openai_response['choices'][0]['message']['content']

            # Add the AI's response to the conversation history
            conversation_history.append(f"AI: {ai_response}")

            # Text back your response!
            resp.message(ai_response)
        except Exception as e:
            print(f"Error: {e}")
            resp.message("Sorry, I couldn't process your request.")

    return str(resp)


max_turns = 5  # Set the maximum number of conversation turns

@app.route("/incoming_call", methods=["POST"])
def incoming_call():
    global conversation_history, turn_count
    conversation_history = []  # Reset the conversation history
    turn_count = 0  # Reset the turn count

    # Generate the initial message using Google Text-to-Speech
    initial_message = "Hello, this your personal assistant. What can I help you with?"
    audio_content = synthesize_text_to_speech(initial_message)

    # Save the audio content as a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", dir=tempfile.gettempdir()) as temp_audio_file:
        temp_audio_file.write(audio_content)
        temp_audio_file_url = url_for("serve_audio", filename=temp_audio_file.name.split("\\")[-1], _external=True)

    twiml_response = VoiceResponse()
    twiml_response.play(temp_audio_file_url)
    twiml_response.gather(input="speech", action="/conversation", method="POST", timeout="6", speechTimeout="1")

    return str(twiml_response)


@app.route("/serve_audio/<path:filename>", methods=["GET"])
def serve_audio(filename):
    return send_from_directory(tempfile.gettempdir(), filename)


@app.route("/conversation", methods=["POST"])
def handle_conversation():
    global conversation_history

    # Get the user input from the POST request
    user_input = request.values.get("SpeechResult", "").strip()
    print(f"User input: {user_input}")  # Log the user input

    # Add the user's response to the conversation history
    conversation_history.append(f"User: {user_input}")

    twiml_response = VoiceResponse()

    try:
        # Pass the user_input to the OpenAI chat model
        openai_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input},  # Use user_input here
            ]
        )

        ai_response = openai_response['choices'][0]['message']['content']

        # Add the AI's response to the conversation history
        conversation_history.append(f"AI: {ai_response}")

        # Generate the message using Google Text-to-Speech
        ai_audio_content = synthesize_text_to_speech(ai_response)

        # Save the AI's response audio content as a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", dir=tempfile.gettempdir()) as temp_audio_file:
            temp_audio_file.write(ai_audio_content)
            ai_audio_file_url = url_for("serve_audio", filename=temp_audio_file.name.split("\\")[-1], _external=True)

        # Generate the prompt using Google Text-to-Speech
        next_prompt = "Would you like to ask another question?"
        next_prompt_audio_content = synthesize_text_to_speech(next_prompt)

        # Save the prompt's audio content as a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", dir=tempfile.gettempdir()) as temp_audio_file:
            temp_audio_file.write(next_prompt_audio_content)
            next_prompt_audio_file_url = url_for("serve_audio", filename=temp_audio_file.name.split("\\")[-1],
                                                 _external=True)

        # Respond with AI feedback
        twiml_response.play(ai_audio_file_url)
        twiml_response.play(next_prompt_audio_file_url)
        twiml_response.gather(input="speech", action="/user_response", method="POST", timeout="2", speechTimeout="1")

    except GoogleAPICallError as e:
        print(f"Google API error: {e}")
        ai_response = "Sorry, I couldn't process your request."
        audio_content = synthesize_text_to_speech(ai_response)

        # Save the error message as a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", dir=tempfile.gettempdir()) as temp_audio_file:
            temp_audio_file.write(audio_content)
            error_audio_file_url = url_for("serve_audio", filename=temp_audio_file.name.split("\\")[-1], _external=True)

        # Respond with the error message
        twiml_response.play(error_audio_file_url)

    return str(twiml_response)


@app.route("/user_response", methods=["POST"])
def user_response():
    # Generate the message using Google Text-to-Speech
    next_question_message = "What is your next question?"
    audio_content = synthesize_text_to_speech(next_question_message)

    # Save the audio content as a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3", dir=tempfile.gettempdir()) as temp_audio_file:
        temp_audio_file.write(audio_content)
        temp_audio_file_url = url_for("serve_audio", filename=temp_audio_file.name.split("\\")[-1], _external=True)

    twiml_response = VoiceResponse()
    twiml_response.play(temp_audio_file_url)
    twiml_response.gather(input="speech", action="/conversation", method="POST", timeout="5", speechTimeout="2")

    return str(twiml_response)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
