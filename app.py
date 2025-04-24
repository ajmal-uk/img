# app.py on Render
from flask import Flask, request, jsonify, Response
import requests

app = Flask(__name__)
API_KEY = "your-secret-api-key"  # Set your own API key

@app.route('/ask-image', methods=['POST'])
def ask_image():
    # Auth check
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
            return Response(trax_response.content, content_type="image/png")
        else:
            return jsonify({"error": "Image generation failed", "status": trax_response.status_code}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
