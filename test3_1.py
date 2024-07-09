from flask import Flask, render_template, request, jsonify
import openai
import os
import base64
from PIL import Image
import requests
import json

app = Flask(__name__)
openai.api_key = 'OPENAI_API_KEY'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api", methods=["POST"])
def chat_api():
    try:
        data = request.get_json()
        print("Received chat message:", data)  # Debugging statement
        message = data.get("message")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}]
        )
        print("OpenAI response:", response)  # Debugging statement
        response_message = response.choices[0].message.content if response.choices else "No response generated."
        return jsonify({"message": response_message})
    except Exception as e:
        print("Error in chat_api:", e)
        return jsonify({"error": "Failed to get response from the server."})

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"})
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"})
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            print("File saved at:", filepath)  # Debugging statement

            with open(filepath, "rb") as image_file:
                image_data = image_file.read()

            image_base64 = base64.b64encode(image_data).decode("utf-8")

            latitude = 49.207
            longitude = 16.608

            payload = {
                "images": [f"data:image/jpg;base64,{image_base64}"],
                "latitude": latitude,
                "longitude": longitude,
                "similar_images": True
            }

            json_payload = json.dumps(payload, indent=4)
            url = "https://plant.id/api/v3/identification"
            headers = {
                'Api-Key': 'PLANT_API_KEY',
                "Content-Type": "application/json"
            }

            response = requests.post(url
            , headers=headers, data=json_payload)
            print("Plant ID API response status:", response.status_code)  # Debugging statement
            print("Plant ID API response body:", response.text)  # Debugging statement

            if response.status_code == 200 or response.status_code == 201:
                plant_data = response.json()
                try:
                    plant_name = plant_data['result']['classification']['suggestions'][0]['name']
                    prompt = f"Give the optimum conditions and measures for {plant_name} to grow, including soil pH, water pH, and how often to water them. List them as bullet points."
                    
                    gpt_response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    response_message = gpt_response.choices[0].message.content if gpt_response.choices else "No response generated."
                    return jsonify({"response": response_message})
                except IndexError:
                    return jsonify({"error": "Could not find plant name in the response."})
            else:
                return jsonify({"error": "Plant ID API request failed"}), response.status_code
    except Exception as e:
        print("Error in upload_file:", e)
        return jsonify({"error": "Failed to get response from the server."})

if __name__ == '__main__':
    app.run(debug=True, port=5002)


