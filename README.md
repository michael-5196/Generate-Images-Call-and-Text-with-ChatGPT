# Generate-Images-Call-and-Text-with-ChatGPT
☎️📱🤖This project is an AI Assistant powered by OpenAI and Google Text-to-Speech that's interfaced thru Twilio for SMS and voice interactions. It’s designed to handle phone call conversations, texts and image generation that let you ultimately communicate with ChatGPT via sms and calls from any phone. 

Additionally, this will also cost money 💲 since you will be using twilio and your own openai api key. 

## Instructions

### Step 1: Clone the Repository

`git clone <repository_url>`

### Step 2: Install the Dependencies
Before you can run your Flask app, they will need to install its dependencies. You can do this by running the following command in the terminal:

```bash
pip install flask twilio google-cloud-texttospeech google-cloud-speech openai

```
### Step 3: Twilio Setup
#### 3a: Sign Up for Twilio
Navigate to [Twilio’s website](https://twilio.com/). Sign up, purchase a number, and complete any necessary registration steps required for SMS.

#### 3b: Get Your SID and Auth Token
Once logged into your Twilio account, you can find your Account SID and Auth Token on your Dashboard. Remember to keep your Auth Token top-secret!

### Step 4: Google Cloud Setup
#### 4a: Sign In or Create a Google Cloud Account
Go to the [Google Cloud Console](https://console.cloud.google.com/).

#### 4b: Create a New Project
Once signed in, create a new project.

#### 4c: Enable the API
Search for the "Speech-to-Text" & "Text-to-Speech" APIs in the library, and enable them for your project.

#### 4d: Create a Service Account and Generate a JSON Key
From the main Cloud Console menu, go to "IAM & Admin" > "Service Accounts". Create a service account, grant it permissions, and generate a JSON key.

#### 4e: Provide the JSON Key to Your Application
Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable in your system to the file location path of your service account key file.

### Step 5: Set Environment Variables
Set the following environment variables in your system:
- `OPENAI_API_KEY`
- `GOOGLE_APPLICATION_CREDENTIALS`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_NUMBER`

### Step 6: Navigate to the Repository
In your terminal: `cd <Your-File-Path-to-the-Repository>`

### Step 7: Run the Application
In your terminal, navigate to the folder where you downloaded the `assistant.py` file and run the application with the following command:
```bash
python assistant.py
```
### Step 8: Start ngrok
To make the Flask application accessible over the internet, you’ll need to download and install ngrok. Use a free plan account. Once you’ve done that, start the ngrok application, type and execute the following command within the ngrok terminal:

```bash
ngrok http 5000
```
### Step 9: Update Twilio Webhooks
You’ll need to set the webhook URLs in your Twilio account to the forwarding URL provided by ngrok. The endpoints /incoming_call and /sms should be appended to the ngrok URL for voice and message services respectively.

### You're all set! Now you can call your Twilio Number and start chatting with the AI assistant.
### To generate images, began the text with img followed by a picture you want to create
### You can choose a different Google Text-To-Speech voice here: (https://cloud.google.com/text-to-speech/docs/voices). Go to the synthesize text-to-speech function and replace the Google voice model with the name of another. 


## Important
Please note for calls that Google has limitations to the number of words it can convert and may be further limited by the specific model chosen. If your assistant incurs an application error, it is likely because of the Google TTS limitation. 

SMS responses may also not send if the responses are too long. Further updates will have a way to chunk the message across multiple sms texts. 
