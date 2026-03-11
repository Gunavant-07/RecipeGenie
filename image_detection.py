import numpy as np
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import tensorflow as tf
from tensorflow.keras.preprocessing import image
import os

model = tf.keras.models.load_model("model/ingredient_model.h5")

dataset_path = "F:/processed_dataset/train"

class_names = sorted(os.listdir(dataset_path))

def detect_ingredient(img_path):

    img = image.load_img(img_path, target_size=(224,224))
    img_array = image.img_to_array(img)

    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0

    predictions = model.predict(img_array)

    predicted_index = np.argmax(predictions)

    return class_names[predicted_index]