from flask import Flask, request, jsonify
import requests
import os
import tempfile
import threading
import base64

app = Flask(__name__)
API_KEY = "byteai-image-gen"  # Replace with your API key

# Path to store the temporary image file
TEMP_DIR = tempfile.gettempdir()

# Function to delete the image after a delay
def delete_image(image_path, delay=600):
    def remove_file():
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"Image {image_path} deleted after timeout.")
    threading.Timer(delay, remove_file).start()

@app.route('/generate-image', methods=['POST'])
def generate_image():
    client_key = request.headers.get("X-API-KEY")
    if client_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    prompt = data.get("prompt")
    if not prompt:
        return jsonify({"error": "Prompt is required."}), 400

    try:
        # Call TraxDinosaur API
        trax_response = requests.post(
            "https://apiimagestrax.vercel.app/api/genimage",
            json={"prompt": prompt},
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if trax_response.status_code == 200:
            temp_image_path = os.path.join(TEMP_DIR, "generated_image.png")
            with open(temp_image_path, "wb") as f:
                f.write(trax_response.content)

            delete_image(temp_image_path, delay=600)

            # Encode image in base64
            with open(temp_image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

            return jsonify({
                "prompt": prompt,
                "image_base64": encoded_string,
                "content_type": "image/png",
                "message": "Image generated successfully."
            })

        else:
            return jsonify({
                "error": "Image generation failed",
                "status": trax_response.status_code
            }), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
#gunicorn==23.0.0
