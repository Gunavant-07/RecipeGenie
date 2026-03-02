import os
import cv2
import random
from PIL import Image

# -------------------------------
# PATHS
# -------------------------------
SOURCE_PATH = r"F:\train dataset"
OUTPUT_PATH = r"F:\processed_dataset"

IMG_SIZE = 224

# Split ratios
TRAIN_SPLIT = 0.7
VAL_SPLIT = 0.2
TEST_SPLIT = 0.1

# -------------------------------
# CREATE OUTPUT FOLDERS
# -------------------------------
for split in ["train", "val", "test"]:
    split_path = os.path.join(OUTPUT_PATH, split)
    os.makedirs(split_path, exist_ok=True)

# -------------------------------
# PROCESS EACH CLASS
# -------------------------------
for class_name in os.listdir(SOURCE_PATH):

    class_path = os.path.join(SOURCE_PATH, class_name)

    if not os.path.isdir(class_path):
        continue

    print(f"\nProcessing class: {class_name}")

    images = []

    # -------------------------------
    # STEP 1: REMOVE CORRUPTED IMAGES
    # -------------------------------
    for file in os.listdir(class_path):
        file_path = os.path.join(class_path, file)

        try:
            img = Image.open(file_path)
            img.verify()
            images.append(file_path)
        except:
            print("Removing corrupted:", file_path)
            os.remove(file_path)

    # Shuffle images
    random.shuffle(images)

    # -------------------------------
    # STEP 2: SPLIT DATA
    # -------------------------------
    total = len(images)
    train_end = int(TRAIN_SPLIT * total)
    val_end = int((TRAIN_SPLIT + VAL_SPLIT) * total)

    train_imgs = images[:train_end]
    val_imgs = images[train_end:val_end]
    test_imgs = images[val_end:]

    # -------------------------------
    # STEP 3: CREATE CLASS FOLDERS
    # -------------------------------
    for split in ["train", "val", "test"]:
        os.makedirs(os.path.join(OUTPUT_PATH, split, class_name), exist_ok=True)

    # -------------------------------
    # STEP 4: PROCESS & SAVE IMAGES
    # -------------------------------
    def process_and_save(img_list, split):
        for img_path in img_list:
            img = cv2.imread(img_path)

            if img is None:
                continue

            # Resize
            img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))

            # Save to new location
            filename = os.path.basename(img_path)
            save_path = os.path.join(OUTPUT_PATH, split, class_name, filename)

            cv2.imwrite(save_path, img)

    process_and_save(train_imgs, "train")
    process_and_save(val_imgs, "val")
    process_and_save(test_imgs, "test")

# -------------------------------
# DONE
# -------------------------------
print("\n✅ Preprocessing + Splitting Completed!")