from ultralytics import YOLO
import cv2

print("Loading YOLO model...")
model = YOLO("yolov8n.pt")
print("Model loaded")


def detect_ingredients_yolo(image_path):

    print("STEP 1: function started")

    img = cv2.imread(image_path)

    if img is None:
        print("ERROR: Image not found")
        return []

    print("STEP 2: running detection")

    results = model(img)

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

    print("STEP 3: detection complete")

    return detected_items


result = detect_ingredients_yolo("static/uploads/6.jpg")
print(result)