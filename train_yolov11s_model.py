import os
import shutil
import random
from ultralytics import YOLO

# ================== PATHS ==================
BASE_PATH = r"F:\recipeGinie web app\auto labeling\raw images"
OUTPUT_PATH = r"F:\recipeGinie web app\train_dataset_50k"

# ================== CONFIG ==================
SPLIT_RATIO = 0.8
IMG_SIZE = 320        # 🔥 reduce for speed
BATCH_SIZE = 2
EPOCHS = 10

# ================== STEP 1: READ CLASSES ==================
print("\n📂 Reading dataset...")

class_names = []
all_data = []

for class_id, folder in enumerate(sorted(os.listdir(BASE_PATH))):
    folder_path = os.path.join(BASE_PATH, folder)

    if os.path.isdir(folder_path):
        class_names.append(folder)

        images = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")]

        for img in images:
            all_data.append((os.path.join(folder_path, img), class_id))

print(f"📊 Total Classes: {len(class_names)}")
print(f"📊 Total Images: {len(all_data)}")

# ================== STEP 2: SHUFFLE & SPLIT ==================
random.shuffle(all_data)

split_index = int(len(all_data) * SPLIT_RATIO)

train_data = all_data[:split_index]
val_data = all_data[split_index:]

print(f"📊 Train: {len(train_data)}")
print(f"📊 Val: {len(val_data)}")

# ================== STEP 3: CREATE FOLDERS ==================
for folder in ['images/train', 'images/val', 'labels/train', 'labels/val']:
    os.makedirs(os.path.join(OUTPUT_PATH, folder), exist_ok=True)

# ================== STEP 4: PROCESS ONLY IF NOT DONE ==================
train_folder = os.path.join(OUTPUT_PATH, "images/train")

if len(os.listdir(train_folder)) == 0:
    print("\n⚙️ Processing dataset...")

    def process(data, split):
        print(f"\n📂 Processing {split}...")

        for i, (img_path, class_id) in enumerate(data):
            file_name = os.path.basename(img_path)

            img_dst = os.path.join(OUTPUT_PATH, f"images/{split}", file_name)
            label_dst = os.path.join(OUTPUT_PATH, f"labels/{split}", file_name.replace(".jpg", ".txt"))

            if not os.path.exists(img_dst):
                shutil.copy(img_path, img_dst)

            if not os.path.exists(label_dst):
                with open(label_dst, "w") as f:
                    f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")

            if (i+1) % 2000 == 0:
                print(f"➡️ {i+1}/{len(data)} done")

    process(train_data, "train")
    process(val_data, "val")

else:
    print("\n✅ Dataset already processed. Skipping...")

# ================== STEP 5: CREATE YAML ==================
yaml_path = os.path.join(OUTPUT_PATH, "dataset.yaml")

with open(yaml_path, "w") as f:
    f.write(f"path: {OUTPUT_PATH}\n")
    f.write("train: images/train\n")
    f.write("val: images/val\n\n")
    f.write("names:\n")

    for i, name in enumerate(class_names):
        f.write(f"  {i}: {name}\n")

print("\n✅ dataset.yaml created")

# ================== STEP 6: TRAIN (RESUME SAFE) ==================
print("\n🚀 Starting Training...")

RUNS_DIR = r"E:\RecipeGenie\RecipeGenie\runs\detect"

def get_last_checkpoint():
    if not os.path.exists(RUNS_DIR):
        return None

    folders = [f for f in os.listdir(RUNS_DIR) if f.startswith("train")]
    folders.sort(reverse=True)

    for folder in folders:
        ckpt = os.path.join(RUNS_DIR, folder, "weights", "last.pt")
        if os.path.exists(ckpt):
            return ckpt
    return None

last_ckpt = get_last_checkpoint()

# 🔁 RESUME
if last_ckpt:
    print(f"🔄 Resuming from: {last_ckpt}")
    model = YOLO(last_ckpt)

    model.train(
        resume=True,
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        device="cpu",
        workers=0,
        cache=True
    )

# 🆕 NEW TRAIN
else:
    print("🆕 Starting fresh training...")
    model = YOLO("yolo11s.pt")

    model.train(
        data=yaml_path,
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        device="cpu",
        workers=0,
        cache=True
    )

print("\n🎉 TRAINING COMPLETED!")