try:
    import cv2
    import numpy as np
    HAVE_CV2 = True
except Exception:
    cv2 = None
    HAVE_CV2 = False
from roboflow import Roboflow
from flask import Flask, render_template, request, Response, redirect, url_for, jsonify, send_from_directory
import os
import uuid  # Add this to generate unique filenames

# Initialize Roboflow with your API key (use your own API key)
rf = Roboflow(api_key="RBMCiagFraeIHPvptwcS")
project = rf.workspace().project("freshness-fruits-and-vegetables")
model = project.version(7).model

# Initialize Flask app
app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')

# Helper function for object detection on an image
def detect_on_image(image_path):
    if not HAVE_CV2:
        raise RuntimeError('OpenCV (cv2) is not available in the environment')
    image = cv2.imread(image_path)
    results = model.predict(image, confidence=40, overlap=30).json()
    
    for prediction in results['predictions']:
        x, y, w, h = (
            prediction['x'], 
            prediction['y'], 
            prediction['width'], 
            prediction['height']
        )
        class_name = prediction['class']
        confidence = prediction['confidence']

        # Calculate bounding box coordinates
        x_min = int(x - w / 2)
        y_min = int(y - h / 2)
        x_max = int(x + w / 2)
        y_max = int(y + h / 2)
        
        # Draw the bounding box
        cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        
        # Create label with class and confidence score
        label = f"{class_name}: {confidence:.2f}"
        
        # Put the label above the bounding box
        cv2.putText(image, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Save the result image with a unique filename
    result_filename = f'result_{uuid.uuid4().hex}.jpg'
    result_image_path = os.path.join(UPLOAD_FOLDER, result_filename)
    cv2.imwrite(result_image_path, image)
    
    return result_image_path

# Route for homepage with detection options
@app.route('/')
def index():
    # If a production React build exists, serve it. Otherwise fall back to Flask templates.
    if os.path.exists(os.path.join(FRONTEND_DIST, 'index.html')):
        return send_from_directory(FRONTEND_DIST, 'index.html')
    return render_template('index.html')

# Route for handling image upload and detection
@app.route('/detect_image', methods=['POST'])
def detect_image():
    if 'image' not in request.files:
        return redirect(request.url)
    
    file = request.files['image']
    
    if file.filename == '':
        return redirect(request.url)
    
    if file:
        # Save the uploaded image
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(image_path)
        
        # Perform detection on the image
        result_image_path = detect_on_image(image_path)
        result_image_filename = os.path.basename(result_image_path)  # Get the filename only
        os.remove(image_path)  # Optionally remove the uploaded image after processing
        
        # Generate a UUID for cache-busting
        unique_id = uuid.uuid4().hex
        
        # If the client expects JSON (fetch from React), return JSON response
        accept = request.headers.get('Accept', '')
        # Return an absolute URL so the frontend dev server can load the image across ports
        image_url = url_for('static', filename=f'uploads/{result_image_filename}', _external=True)
        if 'application/json' in accept or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'result_image': result_image_filename,
                'image_url': image_url,
                'unique_id': unique_id
            })

        # Render the result page with the processed image and UUID for regular browser form posts
        return render_template('result.html', result_image=result_image_filename, unique_id=unique_id)

# Route for handling live webcam feed detection
@app.route('/live_feed')
def live_feed():
    return render_template('live_feed.html')

def generate_live_feed():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        raise IOError("Cannot open webcam")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Resize the frame to 640x640
        frame = cv2.resize(frame, (640, 640))
        
        # Perform inference on each resized frame
        results = model.predict(frame, confidence=40, overlap=30).json()
        
        # Extract bounding boxes and labels from the predictions
        for prediction in results['predictions']:
            x, y, w, h = (
                prediction['x'], 
                prediction['y'], 
                prediction['width'], 
                prediction['height']
            )
            class_name = prediction['class']
            confidence = prediction['confidence']
            
            # Calculate bounding box coordinates
            x_min = int(x - w / 2)
            y_min = int(y - h / 2)
            x_max = int(x + w / 2)
            y_max = int(y + w / 2)
            
            # Draw the bounding box
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            
            # Create label with class and confidence score
            label = f"{class_name}: {confidence:.2f}"
            
            # Put the label above the bounding box
            cv2.putText(frame, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Encode the frame into JPEG format
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        # Yield the frame in byte format for streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@app.route('/video_feed')
def video_feed():
    return Response(generate_live_feed(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Main entry point
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
