

# import os
# import shutil
# import random
# import time
# from ultralytics import YOLO

# # ================== PATHS ==================
# BASE_PATH = r"F:\new recipeginie\images"
# OUTPUT_PATH = r"F:\new recipeginie\dataset"

# # ================== STEP 1: DATASET LOG ==================
# print("\n📂 DATASET STRUCTURE:\n")

# total_images = 0
# class_names = []

# for folder in sorted(os.listdir(BASE_PATH)):
#     folder_path = os.path.join(BASE_PATH, folder)

#     if os.path.isdir(folder_path):
#         count = len([f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")])
#         print(f"{folder} → {count} images")
#         total_images += count
#         class_names.append(folder)

# print(f"\n📊 TOTAL IMAGES: {total_images}")

# # ================== STEP 2: CREATE FOLDERS ==================
# for folder in ['images/train', 'images/val', 'labels/train', 'labels/val']:
#     os.makedirs(os.path.join(OUTPUT_PATH, folder), exist_ok=True)

# # ================== STEP 3: PREPARE DATA ==================
# all_data = []

# for class_id, class_name in enumerate(class_names):
#     class_path = os.path.join(BASE_PATH, class_name)

#     for file in os.listdir(class_path):
#         if file.lower().endswith(".jpg"):
#             all_data.append((os.path.join(class_path, file), class_id))

# random.shuffle(all_data)

# split_ratio = 0.8
# split_index = int(len(all_data) * split_ratio)

# train_data = all_data[:split_index]
# val_data = all_data[split_index:]

# print(f"\n📊 Train Images: {len(train_data)}")
# print(f"📊 Val Images: {len(val_data)}")

# # ================== STEP 4: RESUME-SAFE PROCESSING ==================
# def process_data(data, split):
#     print(f"\n📂 Processing {split.upper()} set...")

#     progress_file = os.path.join(OUTPUT_PATH, f"progress_{split}.txt")

#     start_index = 0
#     if os.path.exists(progress_file):
#         with open(progress_file, "r") as f:
#             start_index = int(f.read().strip())
#         print(f"🔄 Resuming from index: {start_index}")

#     total = len(data)
#     start_time = time.time()

#     for i in range(start_index, total):
#         img_path, class_id = data[i]
#         file_name = os.path.basename(img_path)

#         new_img_path = os.path.join(OUTPUT_PATH, f"images/{split}", file_name)
#         new_label_path = os.path.join(OUTPUT_PATH, f"labels/{split}", file_name.replace(".jpg", ".txt"))

#         try:
#             if not (os.path.exists(new_img_path) and os.path.exists(new_label_path)):
#                 shutil.copy(img_path, new_img_path)

#                 with open(new_label_path, "w") as f:
#                     f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")

#             # Save progress
#             if i % 100 == 0:
#                 with open(progress_file, "w") as f:
#                     f.write(str(i))

#             # Logs
#             if (i + 1) % 500 == 0 or (i + 1) == total:
#                 percent = ((i + 1) / total) * 100
#                 print(f"📊 {split.upper()} Progress: {percent:.2f}% ({i+1}/{total})")

#         except KeyboardInterrupt:
#             print("\n⛔ Stopped manually!")
#             with open(progress_file, "w") as f:
#                 f.write(str(i))
#             return

#     print(f"✅ {split.upper()} COMPLETED")

#     if os.path.exists(progress_file):
#         os.remove(progress_file)

# # ▶️ RUN PROCESSING
# process_data(train_data, "train")
# process_data(val_data, "val")

# # ================== STEP 4.1: SKIP IF ALREADY PROCESSED ==================
# train_folder = os.path.join(OUTPUT_PATH, "images/train")
# val_folder = os.path.join(OUTPUT_PATH, "images/val")

# if len(os.listdir(train_folder)) == 0 or len(os.listdir(val_folder)) == 0:
#     print("\n⚙️ Dataset not found. Processing now...")

#     process_data(train_data, "train")
#     process_data(val_data, "val")

# else:
#     print("\n✅ Dataset already processed. Skipping preprocessing step.")

# # ================== STEP 5: CREATE YAML ==================
# yaml_path = os.path.join(OUTPUT_PATH, "dataset.yaml")

# with open(yaml_path, "w") as f:
#     f.write(f"path: {OUTPUT_PATH}\n")
#     f.write("train: images/train\n")
#     f.write("val: images/val\n\n")
#     f.write("names:\n")

#     for i, name in enumerate(class_names):
#         f.write(f"  {i}: {name}\n")

# print("\n✅ dataset.yaml created")

# # ================== STEP 6: TRAIN WITH EPOCH PROGRESS ==================
# print("\n🚀 STARTING TRAINING WITH CHECKPOINT SYSTEM...")

# RUNS_DIR = r"E:\RecipeGenie\RecipeGenie\runs\detect"

# def get_last_checkpoint():
#     if not os.path.exists(RUNS_DIR):
#         return None

#     folders = [f for f in os.listdir(RUNS_DIR) if f.startswith("train")]
#     if not folders:
#         return None

#     folders.sort(reverse=True)

#     for folder in folders:
#         ckpt_path = os.path.join(RUNS_DIR, folder, "weights", "last.pt")
#         if os.path.exists(ckpt_path):
#             return ckpt_path

#     return None

# last_ckpt = get_last_checkpoint()

# # 🔁 RESUME TRAINING
# if last_ckpt:
#     print(f"🔄 Resuming from checkpoint: {last_ckpt}")

#     model = YOLO(last_ckpt)

#     model.train(
#         resume=True,
#         epochs=20,
#         imgsz=416,
#         batch=2,
#         device="cpu",
#         workers=0,
#         cache=True,
#         save=True,
#         verbose=True
#     )

# # 🆕 NEW TRAINING
# else:
#     print("🆕 Starting fresh training...")

#     model = YOLO("yolo11s.pt")

#     model.train(
#         data=yaml_path,
#         epochs=20,
#         imgsz=416,
#         batch=2,
#         device="cpu",
#         workers=0,
#         cache=True,
#         save=True,
#         verbose=True
#     )

# print("\n🎉 TRAINING COMPLETED!")

# EPOCHS = 20
# model = YOLO("yolo11s.pt")

# start_training = time.time()

# for epoch in range(EPOCHS):
#     print(f"\n🔥 Epoch {epoch+1}/{EPOCHS} STARTED")

#     epoch_start = time.time()

#     model.train(
#         data=yaml_path,
#         epochs=1,            # run one epoch at a time
#         imgsz=640,
#         batch=4,
#         device='cpu',
#         verbose=False
#     )

#     epoch_time = time.time() - epoch_start
#     total_time = time.time() - start_training

#     percent = ((epoch + 1) / EPOCHS) * 100

#     print(f"✅ Epoch {epoch+1} Completed")
#     print(f"📊 Progress: {percent:.2f}%")
#     print(f"⏱️ Epoch Time: {epoch_time/60:.2f} min")
#     print(f"⏳ Total Time: {total_time/60:.2f} min")

# print("\n🎉 TRAINING COMPLETED!")

# print("\n🎉 DONE!")