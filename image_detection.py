# ingredient_detection.py

from ultralytics import YOLO
import cv2

# Load your trained model (change path if needed)
MODEL_PATH = "runs/detect/train/weights/best.pt"

model = YOLO(MODEL_PATH)


def detect_ingredients_from_image(image_path, conf_threshold=0.4):
    """
    Detect ingredients from image path

    Args:
        image_path (str): Path to image
        conf_threshold (float): Confidence threshold

    Returns:
        list: detected ingredient names
    """

    results = model(image_path)

    detected_items = []

    for r in results:
        boxes = r.boxes

        for box in boxes:
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])

            if conf >= conf_threshold:
                label = model.names[cls_id]
                detected_items.append(label)

    # Remove duplicates
    detected_items = list(set(detected_items))

    return detected_items


# OPTIONAL: for Flask (image upload)
def detect_ingredients_from_bytes(image_bytes, conf_threshold=0.4):
    """
    Detect ingredients from uploaded image (bytes)
    """

    import numpy as np

    # Convert bytes → image
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    results = model(img)

    detected_items = []

    for r in results:
        for box in r.boxes:
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])

            if conf >= conf_threshold:
                label = model.names[cls_id]
                detected_items.append(label)

    return list(set(detected_items))


# TEST RUN
if __name__ == "__main__":
    image_path = "test.jpg"  # put any image

    detected = detect_ingredients_from_image(image_path)

    print("Detected Ingredients:", detected)