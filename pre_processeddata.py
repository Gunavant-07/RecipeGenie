import os

DATASET_PATH = r"F:\processed_dataset"

def count_images(folder_path):
    total = 0
    class_counts = {}

    for class_name in os.listdir(folder_path):
        class_path = os.path.join(folder_path, class_name)

        if os.path.isdir(class_path):
            count = len(os.listdir(class_path))
            class_counts[class_name] = count
            total += count

    return total, class_counts


# -------------------------------
# COUNT DATA
# -------------------------------
train_total, train_classes = count_images(os.path.join(DATASET_PATH, "train"))
val_total, val_classes = count_images(os.path.join(DATASET_PATH, "val"))
test_total, test_classes = count_images(os.path.join(DATASET_PATH, "test"))

# -------------------------------
# PRINT LOGS
# -------------------------------
print("\n📊 DATASET SUMMARY\n")

print("🔹 TRAIN DATA:")
print("Total Images:", train_total)
for k, v in train_classes.items():
    print(f"{k}: {v}")

print("\n🔹 VALIDATION DATA:")
print("Total Images:", val_total)
for k, v in val_classes.items():
    print(f"{k}: {v}")

print("\n🔹 TEST DATA:")
print("Total Images:", test_total)
for k, v in test_classes.items():
    print(f"{k}: {v}")

print("\n✅ Done!")