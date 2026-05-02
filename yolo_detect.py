from ultralytics import YOLO
import cv2
import numpy as np

print("Loading YOLO model...")
model = YOLO("runs/detect/train/weights/best.pt")
# model = YOLO("F:/openimage_dataset/data/model/kaggle/working/runs/detect/ingredient_model_v24/weights/best.pt")
print("Model loaded")


def detect_ingredients_yolo(image_input):

    print("STEP 1: function started")

    # 🔥 CASE 1: If input is file path (string)
    if isinstance(image_input, str):
        print("STEP 2: reading from file path")

        img = cv2.imread(image_input)

        if img is None:
            print("ERROR: failed to read image from path")
            return []

    # 🔥 CASE 2: If input is file object (Flask)
    else:
        print("STEP 2: reading from uploaded file")

        image_input.seek(0)
        image_bytes = image_input.read()

        if not image_bytes:
            print("ERROR: image is empty")
            return []

        img_array = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            print("ERROR: OpenCV decode failed")
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

detect_ingredients_yolo("static/uploads/2.jpg")