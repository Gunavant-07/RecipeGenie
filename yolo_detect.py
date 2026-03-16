from ultralytics import YOLO
import cv2
import numpy as np

print("Loading YOLO model...")
model = YOLO("yolov8n.pt")
print("Model loaded")



def detect_ingredients_yolo(image_file):

    print("STEP 1: function started")

    image_file.seek(0)

    image_bytes = image_file.read()

    if not image_bytes:
        print("ERROR: image is empty")
        return []

    print("STEP 2: image received")

    img_array = np.frombuffer(image_bytes, np.uint8)

    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img is None:
        print("ERROR: OpenCV failed to decode image")
        return []

    print("STEP 3: running YOLO detection")

    results = model(img)

    print("STEP 4: detection complete")

    detected_items = []

    for r in results:
        if r.boxes is None:
            continue

        for box in r.boxes:

            cls_id = int(box.cls[0])
            name = model.names[cls_id]
            conf = float(box.conf[0])

            detected_items.append({
                "ingredient": name,
                "confidence": conf
            })

    print("STEP 5: results ready")

    return detected_items

detect_ingredients_yolo("static/uploads/6.jpg")