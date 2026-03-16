import os
import shutil
import random

# dataset paths
raw_dir = r"F:\recipeGinie web app\auto labeling\raw images\images"
output_dir = r"F:\recipeGinie web app\auto labeling\yolo_dataset"

train_ratio = 0.8

os.makedirs(f"{output_dir}/images/train", exist_ok=True)
os.makedirs(f"{output_dir}/images/val", exist_ok=True)
os.makedirs(f"{output_dir}/labels/train", exist_ok=True)
os.makedirs(f"{output_dir}/labels/val", exist_ok=True)

classes = os.listdir(raw_dir)
class_map = {cls: i for i, cls in enumerate(classes)}

for cls in classes:

    img_dir = os.path.join(raw_dir, cls)
    images = os.listdir(img_dir)

    random.shuffle(images)

    split = int(len(images) * train_ratio)

    train_imgs = images[:split]
    val_imgs = images[split:]

    for img_list, subset in [(train_imgs, "train"), (val_imgs, "val")]:

        for img in img_list:

            src = os.path.join(img_dir, img)
            dst = os.path.join(output_dir, "images", subset, img)

            shutil.copy(src, dst)

            label_path = os.path.join(
                output_dir,
                "labels",
                subset,
                os.path.splitext(img)[0] + ".txt"
            )

            class_id = class_map[cls]

            # full image bounding box
            with open(label_path, "w") as f:
                f.write(f"{class_id} 0.5 0.5 1.0 1.0")

print("Dataset conversion complete")
print("Classes:", class_map)