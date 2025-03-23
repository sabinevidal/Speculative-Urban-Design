#!/usr/bin/env python3
import os
import glob
import shutil


def rename_images_in_sample_folders():
    """
    Renames all images in the sample_images directory to follow the pattern:
    movie_name_1.jpg, movie_name_2.jpg, etc.

    Where movie_name is the name of the folder containing the images.
    """
    # Get the base sample_images directory
    base_dir = "sample_images"

    # Make sure the directory exists
    if not os.path.exists(base_dir):
        print(f"Error: {base_dir} directory not found.")
        return

    # List all subfolders (movie folders)
    movie_folders = [
        d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))
    ]

    # Image file extensions to look for
    extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]

    total_renamed = 0

    # Process each movie folder
    for folder in movie_folders:
        # Skip non-directories or hidden directories
        if folder.startswith("."):
            continue

        folder_path = os.path.join(base_dir, folder)
        print(f"\nProcessing folder: {folder}")

        # Collect all image files
        image_files = []
        for ext in extensions:
            image_files.extend(glob.glob(os.path.join(folder_path, f"*{ext}")))
            image_files.extend(glob.glob(os.path.join(folder_path, f"*{ext.upper()}")))

        # Sort files to ensure consistent numbering
        image_files.sort()

        if not image_files:
            print(f"  No images found in {folder}")
            continue

        # Create a backup folder
        backup_folder = os.path.join(folder_path, "_original_files_backup")
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder)

        # Rename each image
        count = 0
        for i, img_path in enumerate(image_files):
            # Get file extension
            _, ext = os.path.splitext(img_path)

            # Create new filename
            new_name = f"{folder.lower()}_{i+1}{ext.lower()}"
            new_path = os.path.join(folder_path, new_name)

            # Skip if file already has the desired name
            if os.path.basename(img_path).lower() == new_name.lower():
                print(
                    f"  Skipping {os.path.basename(img_path)} (already properly named)"
                )
                continue

            # Backup original file
            backup_path = os.path.join(backup_folder, os.path.basename(img_path))
            shutil.copy2(img_path, backup_path)

            # Rename the file
            os.rename(img_path, new_path)
            count += 1
            total_renamed += 1
            print(f"  Renamed: {os.path.basename(img_path)} → {new_name}")

        print(f"  Renamed {count} images in {folder}")

    print(
        f"\nTotal: Renamed {total_renamed} images across {len(movie_folders)} folders"
    )
    print(f"Original files were backed up in _original_files_backup folders")


if __name__ == "__main__":
    rename_images_in_sample_folders()
