import os
import cv2
import random
import shutil
import logging
from tqdm import tqdm
from sklearn.model_selection import train_test_split

# =========================
# CONFIGURATION
# =========================

RAW_DATA_DIR = r"F:\train dataset"
OUTPUT_DIR = r"F:\Proceesd images dataset"

IMAGE_SIZE = 224
TRAIN_RATIO = 0.7
VAL_RATIO = 0.2
TEST_RATIO = 0.1

MIN_WIDTH = 100
MIN_HEIGHT = 100

ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png"]

# =========================
# SETUP LOGGING
# =========================

log_file = os.path.join(OUTPUT_DIR, "processing_log.txt")
os.makedirs(OUTPUT_DIR, exist_ok=True)

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

print("📁 Starting Dataset Processing...")
logging.info("===== DATASET PROCESSING STARTED =====")

# =========================
# CREATE OUTPUT STRUCTURE
# =========================

for split in ["train", "val", "test"]:
    os.makedirs(os.path.join(OUTPUT_DIR, split), exist_ok=True)

# =========================
# PROCESS EACH INGREDIENT FOLDER
# =========================

total_processed = 0
total_removed = 0

ingredient_folders = [
    d for d in os.listdir(RAW_DATA_DIR)
    if os.path.isdir(os.path.join(RAW_DATA_DIR, d))
]

for ingredient in ingredient_folders:
    print(f"\n🔹 Processing ingredient: {ingredient}")
    logging.info(f"Processing ingredient: {ingredient}")

    ingredient_path = os.path.join(RAW_DATA_DIR, ingredient)

    image_files = [
        f for f in os.listdir(ingredient_path)
        if os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS
    ]

    valid_images = []

    # -------------------------
    # CLEAN IMAGES
    # -------------------------

    for img_name in tqdm(image_files):
        img_path = os.path.join(ingredient_path, img_name)

        try:
            img = cv2.imread(img_path)

            if img is None:
                logging.warning(f"Corrupted image removed: {img_path}")
                total_removed += 1
                continue

            h, w, _ = img.shape

            if h < MIN_HEIGHT or w < MIN_WIDTH:
                logging.warning(f"Small image removed: {img_path}")
                total_removed += 1
                continue

            # Resize
            img = cv2.resize(img, (IMAGE_SIZE, IMAGE_SIZE))

            valid_images.append((img_name, img))

        except Exception as e:
            logging.error(f"Error reading image {img_path}: {e}")
            total_removed += 1

    if len(valid_images) == 0:
        continue

    # -------------------------
    # SPLIT DATASET
    # -------------------------

    train_imgs, temp_imgs = train_test_split(
        valid_images, test_size=(1 - TRAIN_RATIO), random_state=42
    )

    val_size_adjusted = VAL_RATIO / (VAL_RATIO + TEST_RATIO)

    val_imgs, test_imgs = train_test_split(
        temp_imgs, test_size=(1 - val_size_adjusted), random_state=42
    )

    splits = {
        "train": train_imgs,
        "val": val_imgs,
        "test": test_imgs
    }

    # -------------------------
    # SAVE IMAGES
    # -------------------------

    for split_name, images in splits.items():
        split_folder = os.path.join(OUTPUT_DIR, split_name, ingredient)
        os.makedirs(split_folder, exist_ok=True)

        for img_name, img in images:
            save_path = os.path.join(split_folder, img_name)
            cv2.imwrite(save_path, img)
            total_processed += 1

    logging.info(
        f"{ingredient} -> Train: {len(train_imgs)}, Val: {len(val_imgs)}, Test: {len(test_imgs)}"
    )

# =========================
# FINAL LOG SUMMARY
# =========================

logging.info(f"Total images processed: {total_processed}")
logging.info(f"Total images removed: {total_removed}")
logging.info("===== DATASET PROCESSING COMPLETED =====")

print("\n✅ DATASET PROCESSING COMPLETED")
print(f"📦 Total processed images: {total_processed}")
print(f"❌ Total removed images: {total_removed}")
print(f"📝 Log file saved at: {log_file}")