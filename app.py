from flask import Flask, request, Response
import requests
import os
import tempfile
import threading

app = Flask(__name__)
API_KEY = "byteai-image-gen"  # Replace with your API key

# Path to store the temporary image file
TEMP_DIR = tempfile.gettempdir()  # Use the system's temp directory for temp files

# Function to delete the image after a set time
def delete_image(image_path, delay=600):
    """
    Deletes the generated image file after a certain delay (default is 10 minutes).
    """
    def remove_file():
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"Image {image_path} has been deleted.")
    
    # Create a timer to delete the file after the specified delay
    timer = threading.Timer(delay, remove_file)
    timer.start()

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
        # Send the request to TraxDinosaur API
        trax_response = requests.post(
            "https://apiimagestrax.vercel.app/api/genimage",
            json={"prompt": prompt},
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if trax_response.status_code == 200:
            # Save the response content (image) to a temporary file
            temp_image_path = os.path.join(TEMP_DIR, "generated_image.png")
            with open(temp_image_path, "wb") as f:
                f.write(trax_response.content)

            # Schedule the image for deletion after 10 minutes (600 seconds)
            delete_image(temp_image_path, delay=600)

            # Return the image as a response to the client
            return Response(trax_response.content, content_type="image/png")
        else:
            return {"error": "Image generation failed", "status": trax_response.status_code}, 500
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)
