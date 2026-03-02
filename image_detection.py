import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from PIL import Image
import numpy as np
import io

model = MobileNetV2(weights='imagenet')

def detect_ingredients_from_image(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    img = img.resize((224, 224))
    img_array = np.array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    predictions = model.predict(img_array)
    decoded = decode_predictions(predictions, top=5)[0]

    detected = [label for _, label, _ in decoded]
    ingredients = [label for label in detected if label in ['apple', 'banana', 'carrot', 'tomato', 'onion', 'potato', 'besan', 'methi']]  # Extend with Gujarat-specific

    return ingredients