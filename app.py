from flask import Flask, request, Response
import requests

app = Flask(__name__)
API_KEY = "byteai-image-gen"  

@app.route('/generate-image', methods=['POST'])
def generate_image():
    client_key = request.headers.get("X-API-KEY")
    if client_key != API_KEY:
        return {"error": "Unauthorized"}, 401

    data = request.get_json()
    prompt = data.get("prompt")
    if not prompt:
        return {"error": "Prompt is required."}, 400

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
            return {"error": "Image generation failed", "status": trax_response.status_code}, 500
    except Exception as e:
        return {"error": str(e)}, 500
