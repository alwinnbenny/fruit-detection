import requests
import base64

api_key = "AIzaSyAeeBmbdc84UpRYAw6gF7mYlNhz3Gq-m0k"
image_path = "C:\\fruit detection\\Freshness_detection\\image.jpg"

# 1. Encode the image to Base64
with open(image_path, "rb") as image_file:
    base64_image = base64.b64encode(image_file.read()).decode('utf-8')

# 2. Prepare the API endpoint and payload
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

payload = {
    "contents": [{
        "parts": [
            {"text": "What is in this image?"},
            {
                "inlineData": {
                    "mimeType": "image/png",
                    "data": base64_image
                }
            }
        ]
    }]
}

# 3. Make the POST request
response = requests.post(url, json=payload)
print(response.json()['candidates'][0]['content']['parts'][0]['text'])