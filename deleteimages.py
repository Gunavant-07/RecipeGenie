import os
import random

# 🔧 Set your main dataset folder path
DATASET_PATH = r"F:\new recipeginie\Pre_processed_dataset\Pre_processed_dataset\images"   # Example: "dataset" (contains class folders inside)

# MAX_IMAGES = 100

# for folder in os.listdir(DATASET_PATH):
#     folder_path = os.path.join(DATASET_PATH, folder)

#     if not os.path.isdir(folder_path):
#         continue

#     # Get all image files
#     images = [f for f in os.listdir(folder_path) 
#               if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

#     total = len(images)
#     print(f"{folder}: {total} images")

#     if total > MAX_IMAGES:
#         random.shuffle(images)

#         # Keep first 100, delete rest
#         for img in images[MAX_IMAGES:]:
#             img_path = os.path.join(folder_path, img)
#             os.remove(img_path)

#         print(f"➡️ Reduced to {MAX_IMAGES}")
#     else:
#         print("✅ No change needed")

# print("\n🎉 Done! All folders now have max 100 images.")


# total_images = 0

# for folder in os.listdir(DATASET_PATH):
#     folder_path = os.path.join(DATASET_PATH, folder)

#     if not os.path.isdir(folder_path):
#         continue

#     # Count image files
#     images = [f for f in os.listdir(folder_path)
#               if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

#     count = len(images)
#     total_images += count

#     print(f"{folder}: {count} images")

# print("\n📊 Total images in dataset:", total_images)