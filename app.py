try:
    import cv2
    import numpy as np
    HAVE_CV2 = True
except Exception:
    cv2 = None
    HAVE_CV2 = False
from roboflow import Roboflow
from flask import Flask, render_template, request, Response, redirect, url_for, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import os
import uuid
import base64

# Initialize Roboflow with your API key (use your own API key)
rf = Roboflow(api_key="RBMCiagFraeIHPvptwcS")
project = rf.workspace().project("freshness-fruits-and-vegetables")
model = project.version(7).model

# --- Post-processing filters ---

# Confidence threshold for Roboflow predictions
CONFIDENCE_THRESHOLD = 45

# Whitelist of valid fruit/vegetable class names from the model.
# Predictions with classes not in this set are discarded.
VALID_CLASSES = {
    # NOTE: class names use SPACES, matching the model's actual output.
    'fresh apple', 'rotten apple',
    'fresh banana', 'rotten banana',
    'fresh orange', 'rotten orange',
    'fresh potato', 'rotten potato',
    'fresh cucumber', 'rotten cucumber',
    'fresh bellpepper', 'rottenbellpepper',  # model concatenates rotten+bellpepper
    'fresh carrot', 'rotten carrot',
    # Add more classes as the model supports them
}

# Load OpenCV Haar cascade for face detection (used to filter false positives)
if HAVE_CV2:
    _cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(_cascade_path)
else:
    face_cascade = None


def compute_iou(box_a, box_b):
    """Compute Intersection-over-Union between two (x_min, y_min, x_max, y_max) boxes."""
    xa = max(box_a[0], box_b[0])
    ya = max(box_a[1], box_b[1])
    xb = min(box_a[2], box_b[2])
    yb = min(box_a[3], box_b[3])
    inter = max(0, xb - xa) * max(0, yb - ya)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def filter_predictions(predictions, image):
    """Remove predictions that overlap with detected faces or have unknown classes."""
    # Detect faces in the image
    face_boxes = []
    if face_cascade is not None:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        for (fx, fy, fw, fh) in faces:
            face_boxes.append((fx, fy, fx + fw, fy + fh))

    filtered = []
    for pred in predictions:
        # Class whitelist check
        class_name = pred['class'].lower().strip()
        if VALID_CLASSES and class_name not in VALID_CLASSES:
            continue

        # Build prediction bounding box
        x, y, w, h = pred['x'], pred['y'], pred['width'], pred['height']
        pred_box = (int(x - w / 2), int(y - h / 2), int(x + w / 2), int(y + h / 2))

        # Reject predictions that overlap significantly with a detected face
        overlaps_face = False
        for fb in face_boxes:
            if compute_iou(pred_box, fb) > 0.3:
                overlaps_face = True
                break
        if overlaps_face:
            continue

        filtered.append(pred)
    return filtered

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'freshness-detection-secret'
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')

# Initialize SocketIO for real-time detection
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')


@socketio.on('detect_frame')
def ws_detect_frame(data):
    """WebSocket handler: receive base64 frame, emit predictions."""
    if not HAVE_CV2:
        emit('detection_result', {'error': 'OpenCV not available'})
        return
    try:
        frame_b64 = data.get('frame', '')
        if ',' in frame_b64:
            frame_b64 = frame_b64.split(',', 1)[1]
        frame_bytes = base64.b64decode(frame_b64)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            emit('detection_result', {'error': 'Could not decode image'})
            return

        results = model.predict(frame, confidence=CONFIDENCE_THRESHOLD, overlap=30).json()
        predictions = filter_predictions(results.get('predictions', []), frame)
        h_frame, w_frame = frame.shape[:2]

        boxes = []
        for pred in predictions:
            x, y, w, h = pred['x'], pred['y'], pred['width'], pred['height']
            boxes.append({
                'class': pred['class'],
                'confidence': round(pred['confidence'], 4),
                'x': round(x / w_frame, 4),
                'y': round(y / h_frame, 4),
                'width': round(w / w_frame, 4),
                'height': round(h / h_frame, 4),
            })

        emit('detection_result', {'predictions': boxes})
    except Exception as e:
        emit('detection_result', {'error': str(e)})

# Helper function for object detection on an image
def detect_on_image(image_path):
    if not HAVE_CV2:
        raise RuntimeError('OpenCV (cv2) is not available in the environment')
    image = cv2.imread(image_path)
    results = model.predict(image, confidence=CONFIDENCE_THRESHOLD, overlap=30).json()

    # Apply post-processing filters (face filter + class whitelist)
    predictions = filter_predictions(results['predictions'], image)
    
    for prediction in predictions:
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

# API endpoint for detecting a single frame (used by client-side webcam)
@app.route('/api/detect_frame', methods=['POST'])
def api_detect_frame():
    """Accept a base64-encoded JPEG frame, return bounding-box predictions as JSON."""
    if not HAVE_CV2:
        return jsonify({'error': 'OpenCV not available'}), 500

    data = request.get_json(silent=True)
    if not data or 'frame' not in data:
        return jsonify({'error': 'Missing "frame" field (base64 JPEG)'}), 400

    try:
        # Decode the base64 frame
        frame_b64 = data['frame']
        # Strip data-URL prefix if present  (e.g. "data:image/jpeg;base64,...")
        if ',' in frame_b64:
            frame_b64 = frame_b64.split(',', 1)[1]
        frame_bytes = base64.b64decode(frame_b64)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({'error': 'Could not decode image'}), 400

        # Run model
        results = model.predict(frame, confidence=CONFIDENCE_THRESHOLD, overlap=30).json()
        predictions = filter_predictions(results.get('predictions', []), frame)

        h_frame, w_frame = frame.shape[:2]

        boxes = []
        for pred in predictions:
            x, y, w, h = pred['x'], pred['y'], pred['width'], pred['height']
            boxes.append({
                'class': pred['class'],
                'confidence': round(pred['confidence'], 4),
                'x': round(x / w_frame, 4),
                'y': round(y / h_frame, 4),
                'width': round(w / w_frame, 4),
                'height': round(h / h_frame, 4),
            })

        return jsonify({'predictions': boxes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Route for handling live webcam feed detection
@app.route('/live_feed')
def live_feed():
    return render_template('live_feed.html')

def generate_live_feed():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        raise IOError("Cannot open webcam")

    frame_count = 0
    DETECT_EVERY_N = 5  # Only call Roboflow every 5th frame
    cached_predictions = []  # Reuse last predictions for in-between frames
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Resize the frame to 640x480 (smaller = faster)
        frame = cv2.resize(frame, (640, 480))
        frame_count += 1
        
        # Only call Roboflow API every Nth frame
        if frame_count % DETECT_EVERY_N == 1:
            try:
                # Send a smaller image to Roboflow for faster processing
                small = cv2.resize(frame, (320, 240))
                results = model.predict(small, confidence=CONFIDENCE_THRESHOLD, overlap=30).json()
                cached_predictions = filter_predictions(results.get('predictions', []), small)
                # Scale predictions back to full frame size
                for pred in cached_predictions:
                    pred['x'] = pred['x'] * (640 / 320)
                    pred['y'] = pred['y'] * (480 / 240)
                    pred['width'] = pred['width'] * (640 / 320)
                    pred['height'] = pred['height'] * (480 / 240)
            except Exception as e:
                print(f"Detection error: {e}")
        
        # Draw cached predictions on EVERY frame
        for prediction in cached_predictions:
            x, y, w, h = (
                prediction['x'], 
                prediction['y'], 
                prediction['width'], 
                prediction['height']
            )
            class_name = prediction['class']
            confidence = prediction['confidence']
            is_fresh = class_name.lower().startswith('fresh')
            color = (0, 200, 80) if is_fresh else (0, 0, 230)  # Green or Red (BGR)
            
            # Calculate bounding box coordinates
            x_min = int(x - w / 2)
            y_min = int(y - h / 2)
            x_max = int(x + w / 2)
            y_max = int(y + h / 2)
            
            # Draw the bounding box
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), color, 2)
            
            # Semi-transparent fill
            overlay = frame.copy()
            cv2.rectangle(overlay, (x_min, y_min), (x_max, y_max), color, -1)
            cv2.addWeighted(overlay, 0.1, frame, 0.9, 0, frame)
            
            # Create label with class and confidence score
            label = f"{class_name}: {confidence:.0%}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            
            # Label background
            cv2.rectangle(frame, (x_min, y_min - th - 10), (x_min + tw + 8, y_min), color, -1)
            cv2.putText(frame, label, (x_min + 4, y_min - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        
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
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
