import cv2
import numpy as np
from roboflow import Roboflow

# Initialize Roboflow
# do not use this key please make an account for api key in RoboFlow
rf = Roboflow(api_key="RBMCiagFraeIHPvptwcS")
project = rf.workspace().project("freshness-fruits-and-vegetables")
model = project.version(7).model

# --- Post-processing filters ---
CONFIDENCE_THRESHOLD = 45

VALID_CLASSES = {
    'fresh apple', 'rotten apple',
    'fresh banana', 'rotten banana',
    'fresh orange', 'rotten orange',
    'fresh potato', 'rotten potato',
    'fresh cucumber', 'rotten cucumber',
    'fresh bellpepper', 'rottenbellpepper',
    'fresh carrot', 'rotten carrot',
}

# Face detection cascade for filtering out non-fruit regions
_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(_cascade_path)


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


def filter_predictions(predictions, frame):
    """Remove predictions that overlap with detected faces or have unknown classes."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    face_boxes = [(fx, fy, fx + fw, fy + fh) for (fx, fy, fw, fh) in faces]

    filtered = []
    for pred in predictions:
        class_name = pred['class'].lower().strip()
        if VALID_CLASSES and class_name not in VALID_CLASSES:
            continue

        x, y, w, h = pred['x'], pred['y'], pred['width'], pred['height']
        pred_box = (int(x - w / 2), int(y - h / 2), int(x + w / 2), int(y + h / 2))

        overlaps_face = any(compute_iou(pred_box, fb) > 0.3 for fb in face_boxes)
        if overlaps_face:
            continue

        filtered.append(pred)
    return filtered


# Initialize webcam
cap = cv2.VideoCapture(0)

# Check if the webcam is opened correctly
if not cap.isOpened():
    raise IOError("Cannot open webcam")

while True:
    try:
        # Read frame from webcam
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Perform inference
        results = model.predict(frame, confidence=CONFIDENCE_THRESHOLD, overlap=30).json()

        # Apply post-processing filters
        predictions = filter_predictions(results['predictions'], frame)

        # Extract bounding boxes and labels from the predictions
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
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            
            # Create label with class and confidence score
            label = f"{class_name}: {confidence:.2f}"
            
            # Put the label above the bounding box
            cv2.putText(frame, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Display the frame with annotations
        cv2.imshow("Freshness Detection", frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        break

# Release the webcam and close OpenCV windows
cap.release()
cv2.destroyAllWindows()
