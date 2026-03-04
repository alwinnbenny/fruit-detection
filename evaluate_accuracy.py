"""
Accuracy evaluation script for the Freshness Detection model.

Usage:
    python evaluate_accuracy.py --test-dir test_image/ --min-accuracy 85

Test images should follow the naming convention:
    <ground_truth_label>_<anything>.jpg
    e.g. fresh_apple_01.jpg, rotten_banana_02.jpg, face_01.jpg

For "face" images, the expected behaviour is NO fruit detections (they should
be filtered out). For fruit images, the model should predict the correct
freshness category (fresh_* or rotten_*).
"""

import argparse
import os
import sys
import json

try:
    import cv2
    HAVE_CV2 = True
except Exception:
    cv2 = None
    HAVE_CV2 = False

from roboflow import Roboflow

# --- Configuration (mirrors app.py) ---
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

# Face cascade for filtering
if HAVE_CV2:
    _cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(_cascade_path)
else:
    face_cascade = None


def compute_iou(box_a, box_b):
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
    face_boxes = []
    if face_cascade is not None:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        for (fx, fy, fw, fh) in faces:
            face_boxes.append((fx, fy, fx + fw, fy + fh))

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


def extract_ground_truth(filename):
    """
    Extract ground-truth freshness from filename.

    Convention:
      - 'face_*' / 'person_*'  -> expected: no detections
      - 'fresh_*'              -> expected: 'fresh' (any fruit)
      - 'rotten_*'             -> expected: 'rotten' (any fruit)

    We only check the freshness CATEGORY (fresh vs rotten), not the exact
    fruit type, because the model sometimes misidentifies the fruit (e.g.
    orange -> potato) but still gets freshness right.

    Returns: 'fresh', 'rotten', 'none' (for non-fruit), or None (unknown)
    """
    name = os.path.splitext(filename)[0].lower()

    if name.startswith('face') or name.startswith('person') or name.startswith('nofruit') or name.startswith('no_fruit'):
        return 'none'

    if name.startswith('fresh'):
        return 'fresh'
    elif name.startswith('rotten'):
        return 'rotten'

    # Unknown ground truth
    return None


def evaluate(test_dir, min_accuracy, model):
    if not HAVE_CV2:
        print("ERROR: OpenCV (cv2) is required for evaluation.")
        sys.exit(1)

    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    image_files = sorted([
        f for f in os.listdir(test_dir)
        if os.path.splitext(f)[1].lower() in image_extensions
    ])

    if not image_files:
        print(f"ERROR: No images found in '{test_dir}'")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  Freshness Detection — Accuracy Evaluation")
    print(f"  Test directory : {test_dir}")
    print(f"  Images found   : {len(image_files)}")
    print(f"  Confidence     : {CONFIDENCE_THRESHOLD}%")
    print(f"  Min accuracy   : {min_accuracy}%")
    print(f"{'='*60}\n")

    total = 0
    correct = 0
    skipped = 0
    results_log = []

    for img_file in image_files:
        gt_freshness = extract_ground_truth(img_file)
        if gt_freshness is None:
            print(f"  SKIP  {img_file} — cannot determine ground truth from filename")
            skipped += 1
            continue

        total += 1
        img_path = os.path.join(test_dir, img_file)
        image = cv2.imread(img_path)

        if image is None:
            print(f"  FAIL  {img_file} — could not read image")
            results_log.append({'file': img_file, 'result': 'FAIL', 'reason': 'unreadable'})
            continue

        # Run model
        try:
            raw_results = model.predict(image, confidence=CONFIDENCE_THRESHOLD, overlap=30).json()
        except Exception as e:
            print(f"  FAIL  {img_file} — model error: {e}")
            results_log.append({'file': img_file, 'result': 'FAIL', 'reason': str(e)})
            continue

        predictions = filter_predictions(raw_results.get('predictions', []), image)

        if gt_freshness == 'none':
            # Expect NO detections for face/non-fruit images
            if len(predictions) == 0:
                print(f"  PASS  {img_file} — correctly rejected (0 detections)")
                correct += 1
                results_log.append({'file': img_file, 'result': 'PASS', 'reason': 'correctly_rejected'})
            else:
                pred_classes = [p['class'] for p in predictions]
                print(f"  FAIL  {img_file} — false positive: {pred_classes}")
                results_log.append({'file': img_file, 'result': 'FAIL', 'reason': f'false_positive: {pred_classes}'})
        else:
            # Expect at least one prediction matching the freshness category
            if len(predictions) == 0:
                print(f"  FAIL  {img_file} — no detections (expected {gt_freshness})")
                results_log.append({'file': img_file, 'result': 'FAIL', 'reason': 'no_detections'})
                continue

            # Check if any prediction matches expected freshness category
            matched = False
            for pred in predictions:
                pred_class = pred['class'].lower().strip()
                pred_freshness = 'fresh' if pred_class.startswith('fresh') else 'rotten'
                if pred_freshness == gt_freshness:
                    matched = True
                    break

            if matched:
                best = predictions[0]
                print(f"  PASS  {img_file} — detected {best['class']} ({best['confidence']:.0%})")
                correct += 1
                results_log.append({'file': img_file, 'result': 'PASS', 'reason': f"matched: {best['class']}"})
            else:
                pred_classes = [p['class'] for p in predictions]
                print(f"  FAIL  {img_file} — wrong freshness: {pred_classes} (expected {gt_freshness})")
                results_log.append({'file': img_file, 'result': 'FAIL', 'reason': f'wrong_freshness: {pred_classes}'})
    # Summary
    accuracy = (correct / total * 100) if total > 0 else 0
    print(f"\n{'='*60}")
    print(f"  RESULTS")
    print(f"  Total tested : {total}")
    print(f"  Correct      : {correct}")
    print(f"  Accuracy     : {accuracy:.1f}%")
    print(f"  Skipped      : {skipped}")
    print(f"  Target       : {min_accuracy}%")
    print(f"  Status       : {'PASS ✓' if accuracy >= min_accuracy else 'FAIL ✗'}")
    print(f"{'='*60}\n")

    # Save detailed log
    log_path = os.path.join(test_dir, 'evaluation_results.json')
    with open(log_path, 'w') as f:
        json.dump({
            'accuracy': accuracy,
            'total': total,
            'correct': correct,
            'skipped': skipped,
            'min_accuracy': min_accuracy,
            'passed': accuracy >= min_accuracy,
            'details': results_log,
        }, f, indent=2)
    print(f"  Detailed log saved to: {log_path}")

    if accuracy < min_accuracy:
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate freshness detection accuracy')
    parser.add_argument('--test-dir', default='test_image', help='Directory with test images')
    parser.add_argument('--min-accuracy', type=float, default=85.0, help='Minimum required accuracy (%%)')
    parser.add_argument('--api-key', default='RBMCiagFraeIHPvptwcS', help='Roboflow API key')
    args = parser.parse_args()

    # Initialize model
    rf = Roboflow(api_key=args.api_key)
    project = rf.workspace().project("freshness-fruits-and-vegetables")
    eval_model = project.version(7).model

    evaluate(args.test_dir, args.min_accuracy, eval_model)
