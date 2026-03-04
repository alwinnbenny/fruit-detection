"""
Download sample test images for evaluating the freshness detection model.
Images are sourced from freely-available URLs (e.g. Unsplash, Pexels, Wikimedia).
Each file is named with the ground-truth label so evaluate_accuracy.py can parse it.
"""

import os
import urllib.request
import ssl

# Bypass SSL verification for simple image downloads
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "test_image")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# (filename, url) pairs — filenames must start with ground-truth label
# Using freely available images from Unsplash/Pexels with direct CDN links
IMAGES = [
    # Fresh apples
    ("fresh_apple_01.jpg",
     "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400&q=80"),
    ("fresh_apple_02.jpg",
     "https://images.unsplash.com/photo-1567306226416-28f0efdc88ce?w=400&q=80"),
    ("fresh_apple_03.jpg",
     "https://images.unsplash.com/photo-1584306670957-acf935f5033c?w=400&q=80"),
    
    # Fresh bananas
    ("fresh_banana_01.jpg",
     "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&q=80"),
    ("fresh_banana_02.jpg",
     "https://images.unsplash.com/photo-1603833665858-e61d17a86224?w=400&q=80"),
    ("fresh_banana_03.jpg",
     "https://images.unsplash.com/photo-1481349518771-20055b2a7b24?w=400&q=80"),

    # Fresh oranges
    ("fresh_orange_01.jpg",
     "https://images.unsplash.com/photo-1547514701-42782101795e?w=400&q=80"),
    ("fresh_orange_02.jpg",
     "https://images.unsplash.com/photo-1582979512210-99b6a53386f9?w=400&q=80"),
    ("fresh_orange_03.jpg",
     "https://images.unsplash.com/photo-1611080626919-7cf5a9dbab5b?w=400&q=80"),

    # Fresh strawberry
    ("fresh_strawberry_01.jpg",
     "https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=400&q=80"),
    ("fresh_strawberry_02.jpg",
     "https://images.unsplash.com/photo-1543528176-61b239494933?w=400&q=80"),

    # Fresh tomato
    ("fresh_tomato_01.jpg",
     "https://images.unsplash.com/photo-1546470427-0d4db154cdb8?w=400&q=80"),
    ("fresh_tomato_02.jpg",
     "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=400&q=80"),

    # Rotten apple
    ("rotten_apple_01.jpg",
     "https://images.unsplash.com/photo-1601493700631-2b16ec4b4716?w=400&q=80"),

    # Rotten banana (overripe / brown)
    ("rotten_banana_01.jpg",
     "https://images.unsplash.com/photo-1585132757768-5332e4159fd5?w=400&q=80"),
    ("rotten_banana_02.jpg",
     "https://images.unsplash.com/photo-1612363703820-71c4a0fd7034?w=400&q=80"),

    # Face images (should produce 0 fruit detections)
    ("face_01.jpg",
     "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&q=80"),
    ("face_02.jpg",
     "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&q=80"),
    ("face_03.jpg",
     "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&q=80"),
    ("face_04.jpg",
     "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&q=80"),

    # More fresh fruit variety
    ("fresh_mango_01.jpg",
     "https://images.unsplash.com/photo-1553279768-865429fa0078?w=400&q=80"),
    ("fresh_cucumber_01.jpg",
     "https://images.unsplash.com/photo-1449300079323-02e209d9d3a6?w=400&q=80"),
]

downloaded = 0
failed = 0

for filename, url in IMAGES:
    filepath = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(filepath):
        print(f"  EXISTS  {filename}")
        downloaded += 1
        continue
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = resp.read()
        with open(filepath, 'wb') as f:
            f.write(data)
        print(f"  OK      {filename} ({len(data)//1024} KB)")
        downloaded += 1
    except Exception as e:
        print(f"  FAIL    {filename} — {e}")
        failed += 1

print(f"\nDone: {downloaded} downloaded, {failed} failed")
print(f"Test images saved to: {OUTPUT_DIR}")
