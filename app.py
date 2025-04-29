from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import tempfile
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

API_KEY = "byte-ai-image-gen"  # Replace with your real secret key

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
