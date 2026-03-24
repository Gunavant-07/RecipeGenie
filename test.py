import os

base_path = r"F:\recipeGinie web app\Pre_processed_dataset\images"

for folder in os.listdir(base_path):
    folder_path = os.path.join(base_path, folder)

    if os.path.isdir(folder_path):
        files = os.listdir(folder_path)

        # STEP 1: Rename to temp names
        for i, file in enumerate(files):
            old_path = os.path.join(folder_path, file)
            temp_path = os.path.join(folder_path, f"temp_{i}.tmp")
            os.rename(old_path, temp_path)

        # STEP 2: Rename to final names
        temp_files = os.listdir(folder_path)

        for i, file in enumerate(temp_files):
            old_path = os.path.join(folder_path, file)
            new_name = f"{folder}_{i+1}.jpg"  # or keep ext if needed
            new_path = os.path.join(folder_path, new_name)

            os.rename(old_path, new_path)
            print(f"{file} → {new_name}")

print("Perfect renaming done ✅")