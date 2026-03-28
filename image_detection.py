# ==========================================
# IMAGE DETECTION USING YOLO (Ultralytics)
# ==========================================

from ultralytics import YOLO
import cv2
import numpy as np

# ==========================================
# LOAD TRAINED MODEL
# ==========================================

# ⚠️ CHANGE THIS PATH TO YOUR MODEL
MODEL_PATH = r"E:\RecipeGenie\RecipeGenie\runs\detect\train\weights\best.pt"

model = YOLO(MODEL_PATH)


# ==========================================
# DETECT FROM IMAGE PATH (OPTIONAL)
# ==========================================

def detect_ingredients_from_image(image_path, conf_threshold=0.4):

    results = model(image_path)

    detected_items = []

    for r in results:
        for box in r.boxes:

            conf = float(box.conf[0])
            cls_id = int(box.cls[0])

            if conf >= conf_threshold:
                label = model.names[cls_id]
                detected_items.append(label)

    # remove duplicates
    return list(set(detected_items))


# ==========================================
# DETECT FROM IMAGE BYTES (FOR FLASK)
# ==========================================

def detect_ingredients_from_bytes(image_bytes, conf_threshold=0.4):

    # Convert bytes → numpy image
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        return []

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


# ==========================================
# OPTIONAL: RETURN FULL DETAILS (ADVANCED)
# ==========================================

def detect_full_details(image_bytes, conf_threshold=0.4):

    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    results = model(img)

    detections = []

    for r in results:
        for box in r.boxes:

            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            label = model.names[cls_id]

            if conf >= conf_threshold:
                detections.append({
                    "label": label,
                    "confidence": round(conf, 2)
                })

    return detections


# ==========================================
# GET ALL CLASS NAMES (OPTIONAL)
# ==========================================

def get_all_ingredient_names():
    return list(model.names.values())


# ==========================================
# TEST RUN (OPTIONAL)
# ==========================================

if __name__ == "__main__":

    test_image = r"test.jpg"  # put any image

    result = detect_ingredients_from_image(test_image)

    print("Detected:", result)

# # ingredient_detection.py

# from ultralytics import YOLO
# import cv2

# # Load your trained model (change path if needed)
# MODEL_PATH = r"E:\RecipeGenie\RecipeGenie\runs\detect\train\weights\best.pt"

# model = YOLO(MODEL_PATH)


# def detect_ingredients_from_image(image_path, conf_threshold=0.4):
#     """
#     Detect ingredients from image path

#     Args:
#         image_path (str): Path to image
#         conf_threshold (float): Confidence threshold

#     Returns:
#         list: detected ingredient names
#     """

#     results = model(image_path)

#     detected_items = []

#     for r in results:
#         boxes = r.boxes

#         for box in boxes:
#             conf = float(box.conf[0])
#             cls_id = int(box.cls[0])

#             if conf >= conf_threshold:
#                 label = model.names[cls_id]
#                 detected_items.append(label)

#     # Remove duplicates
#     detected_items = list(set(detected_items))

#     return detected_items


# # OPTIONAL: for Flask (image upload)
# def detect_ingredients_from_bytes(image_bytes, conf_threshold=0.4):
#     """
#     Detect ingredients from uploaded image (bytes)
#     """

#     import numpy as np

#     # Convert bytes → image
#     np_arr = np.frombuffer(image_bytes, np.uint8)
#     img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

#     results = model(img)

#     detected_items = []

#     for r in results:
#         for box in r.boxes:
#             conf = float(box.conf[0])
#             cls_id = int(box.cls[0])

#             if conf >= conf_threshold:
#                 label = model.names[cls_id]
#                 detected_items.append(label)

#     return list(set(detected_items))


# # TEST RUN
# if __name__ == "__main__":
#     image_path = "static/uploads/apple3.jpg"
#     # image_path = "test.jpg"  # put any image

#     detected = detect_ingredients_from_image(image_path)

#     print("Detected Ingredients:", detected)