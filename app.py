from bs4 import BeautifulSoup
from gtts import gTTS
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import requests
import tempfile
import os
from gtts.lang import tts_langs

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

API_KEY = "byte-ai-image-gen"  # Replace with your real secret key

app = Flask(__name__)
CORS(app)

API_KEY = "byte-ai-image-gen"  # Replace with your real secret key

SUPPORTED_LANGUAGES = ['en', 'es', 'fr', 'de', 'it']

@app.route('/speak', methods=['POST'])
def speak():
    data = request.json
    text = data.get('text', '')
    voice_input = data.get('voice', 'en|com').strip()

    # Parse voice input into language and tld
    if '|' in voice_input:
        lang, tld = voice_input.split('|', 1)
    else:
        lang = voice_input
        tld = 'com'  # Default tld

    # Validate language code
    if lang not in SUPPORTED_LANGUAGES:
        lang = 'en'
        tld = 'com'

    print("Original text:", text)
    processed_text = process_text_for_speech(text)

    try:
        tts = gTTS(processed_text, lang=lang, tld=tld)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmpfile:
            audio_path = tmpfile.name
            tts.save(audio_path)

        def generate():
            with open(audio_path, 'rb') as f:
                yield from f
            os.remove(audio_path)

        return Response(generate(), mimetype='audio/mpeg')

    except Exception as e:
        print(f"Error generating speech: {str(e)}")
        return jsonify({'error': 'Failed to generate speech'}), 500

def process_text_for_speech(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    for table in soup.find_all('table'):
        table.replace_with("... You can see the table with data in the interface ... ")
    for pre in soup.find_all('pre'):
        pre.replace_with("... Code snippet is available in the interface ... ")
    clean_text = soup.get_text(separator=' ', strip=True)
    expressive_text = clean_text.replace('?', '? ... ')
    expressive_text = expressive_text.replace('!', '! ... ')
    expressive_text = expressive_text.replace('.', '. ... ')
    expressive_text = expressive_text.replace('User', 'User ... ')
    emphasis_words = ['important', 'note', 'warning', 'error', 'success']
    for word in emphasis_words:
        expressive_text = expressive_text.replace(word, f"{word} ... ")
    expressive_text = "... " + expressive_text
    print("Processed text:", expressive_text)
    return expressive_text

@app.route('/voices', methods=['GET'])
def get_voices():
    try:
        languages = tts_langs()
        voice_list = [{'id': code, 'name': name} for code, name in languages.items()]
        return jsonify({'voices': voice_list})
    except Exception as e:
        print(f"Error getting voices: {str(e)}")
        return jsonify({'error': 'Failed to get voices'}), 500

# ---------------- IMAGE GENERATOR ROUTE ----------------
@app.route('/ask-image', methods=['POST'])
def ask_image():
    # API Key check
    if request.headers.get("X-API-KEY") != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    prompt = data.get("prompt")

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    try:
        trax_response = requests.post(
            "https://apiimagestrax.vercel.app/api/genimage",
            json={"prompt": prompt},
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if trax_response.status_code == 200:
            # Save image temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_file.write(trax_response.content)
                temp_filename = tmp_file.name

            # Send file back to user
            response = send_file(temp_filename, mimetype='image/png')

            # Delete file after sending
            @response.call_on_close
            def cleanup():
                try:
                    os.remove(temp_filename)
                except Exception as e:
                    print(f"Error deleting temp file: {e}")

            return response

        else:
            return jsonify({
                "error": "Image generation failed",
                "status": trax_response.status_code,
                "details": trax_response.text
            }), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- CHATBOT ROUTE ----------------
@app.route('/ask-chat', methods=['POST'])
def ask_chat():
    # API Key check
    if request.headers.get("X-API-KEY") != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    prompt = data.get("prompt")
    role = data.get("role", None)  # role is optional

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    try:
        chatbot_response = requests.post(
            "https://apichatbotrax.vercel.app/api/ask",
            json={
                "prompt": prompt,
                "role": role
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if chatbot_response.status_code == 200:
            return jsonify(chatbot_response.json())
        else:
            return jsonify({
                "error": "Chatbot request failed",
                "status": chatbot_response.status_code,
                "details": chatbot_response.text
            }), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- HEALTH CHECK ----------------
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "Byte AI Image + Chatbot API is running!",
        "endpoints": ["/ask-image", "/ask-chat"]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
