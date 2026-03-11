import os
import cv2
import logging
import numpy as np
from tqdm import tqdm
from sklearn.metrics import classification_report

import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import Model

# =====================================
# CONFIG
# =====================================

DATASET_PATH = r"F:\Proceesd images dataset"

TRAIN_DIR = os.path.join(DATASET_PATH, "train")
VAL_DIR = os.path.join(DATASET_PATH, "val")

IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 5

LOG_FILE = "dataset_analysis_log.txt"

# =====================================
# LOGGING SETUP
# =====================================

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

print("Starting dataset analysis...")

# =====================================
# DATASET STATISTICS
# =====================================

print("\n📊 DATASET STATISTICS")

total_images = 0
class_counts = {}

for class_name in os.listdir(TRAIN_DIR):

    class_folder = os.path.join(TRAIN_DIR, class_name)

    if not os.path.isdir(class_folder):
        continue

    images = os.listdir(class_folder)

    count = len(images)

    class_counts[class_name] = count
    total_images += count

    logging.info(f"{class_name} : {count} images")

    print(f"{class_name} → {count} images")

print("\nTotal Training Images:", total_images)
logging.info(f"Total images: {total_images}")

# =====================================
# IMAGE QUALITY CHECK
# =====================================

print("\n🔎 Checking corrupted / blurry images")

corrupted = 0
blurry = 0

def is_blurry(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance < 50

for class_name in os.listdir(TRAIN_DIR):

    folder = os.path.join(TRAIN_DIR, class_name)

    for img_name in tqdm(os.listdir(folder)):

        img_path = os.path.join(folder, img_name)

        try:
            img = cv2.imread(img_path)

            if img is None:
                corrupted += 1
                logging.warning(f"Corrupted image: {img_path}")
                continue

            if is_blurry(img):
                blurry += 1

        except:
            corrupted += 1

print("\nCorrupted images:", corrupted)
print("Blurry images:", blurry)

logging.info(f"Corrupted images: {corrupted}")
logging.info(f"Blurry images: {blurry}")

# =====================================
# DATA GENERATORS
# =====================================

train_gen = ImageDataGenerator(
    rescale=1./255
)

val_gen = ImageDataGenerator(
    rescale=1./255
)

train_data = train_gen.flow_from_directory(
    TRAIN_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode="categorical"
)

val_data = val_gen.flow_from_directory(
    VAL_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode="categorical"
)

num_classes = len(train_data.class_indices)

print("\nClasses:", train_data.class_indices)

# =====================================
# MODEL (MobileNetV2)
# =====================================

base_model = MobileNetV2(
    weights="imagenet",
    include_top=False,
    input_shape=(IMG_SIZE, IMG_SIZE, 3)
)

x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(128, activation="relu")(x)
predictions = Dense(num_classes, activation="softmax")(x)

model = Model(inputs=base_model.input, outputs=predictions)

model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

print("\n🚀 Training quick evaluation model...")

history = model.fit(
    train_data,
    validation_data=val_data,
    epochs=EPOCHS
)

# =====================================
# FINAL ACCURACY
# =====================================

val_loss, val_accuracy = model.evaluate(val_data)

print("\n🎯 DATASET ACCURACY:", val_accuracy)

logging.info(f"Validation accuracy: {val_accuracy}")
with open(LOG_FILE, "a") as f:
    f.write("\n====================================\n")
    f.write("FINAL DATASET EVALUATION\n")
    f.write(f"Validation Loss: {val_loss}\n")
    f.write(f"Validation Accuracy: {val_accuracy}\n")
    f.write("====================================\n")

print("\nAccuracy saved in:", LOG_FILE)

print("\nLogs saved in:", LOG_FILE)