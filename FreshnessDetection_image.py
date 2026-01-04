import cv2
import os
from roboflow import Roboflow

# Initialize Roboflow with your API key (replace with your own key)
rf = Roboflow(api_key="RBMCiagFraeIHPvptwcS")
project = rf.workspace().project("freshness-fruits-and-vegetables")
model = project.version(7).model

# Path to the directory containing images
image_dir = "test_image"

# List all image files in the directory
image_files = [f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]

# Process each image in the directory
for image_file in image_files:
    image_path = os.path.join(image_dir, image_file)
    
    # Read the image
    image = cv2.imread(image_path)
    image = cv2.resize(image, (416, 416)) 
    if image is None:
        print(f"Failed to load image: {image_file}")
        continue

    try:
        # Perform inference on the image
        results = model.predict(image, confidence=40, overlap=30).json()

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
            y_max = int(y + h / 2)

            # Draw the bounding box on the image
            cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

            # Create label with class and confidence score
            label = f"{class_name}: {confidence:.2f}"

            # Put the label above the bounding box
            cv2.putText(image, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Display the image with the bounding boxes and labels
        cv2.imshow(f"Detection - {image_file}", image)
        
        # Wait for a key press to close the image window
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    except Exception as e:
        print(f"An error occurred while processing {image_file}: {str(e)}")

# Optionally close all windows after processing all images
cv2.destroyAllWindows()
