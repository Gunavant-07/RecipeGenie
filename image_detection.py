from ultralytics import YOLO
from PIL import Image
import numpy as np
import io

# Load trained YOLO model
model = YOLO("models/best.pt")   # path to your trained ingredient model


def detect_ingredients_from_image(image_bytes):

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_np = np.array(image)

    results = model(img_np)

    detected = []

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            label = model.names[cls]
            confidence = float(box.conf[0])

            detected.append({
                "ingredient": label,
                "confidence": round(confidence, 3)
            })

    return detected