import os

# Get the folder where the script is located
directory = os.path.dirname(os.path.abspath(__file__))

# Get folder name and remove spaces
folder_name = os.path.basename(directory).replace(" ", "")

# Create prefix
PREFIX = folder_name + "_"

renamed_count = 0
skipped_count = 0

for filename in os.listdir(directory):
    full_path = os.path.join(directory, filename)

    if os.path.isfile(full_path):

        # Skip the script itself
        if filename == os.path.basename(__file__):
            continue

        # Skip if already has prefix
        if filename.startswith(PREFIX):
            print(f"Skipped (already has prefix): {filename}")
            skipped_count += 1
            continue

        new_filename = PREFIX + filename
        new_path = os.path.join(directory, new_filename)

        if not os.path.exists(new_path):
            os.rename(full_path, new_path)
            print(f"Renamed: {filename} -> {new_filename}")
            renamed_count += 1
        else:
            print(f"Skipped (name exists): {new_filename}")
            skipped_count += 1

print("\nFinished.")
print(f"Renamed: {renamed_count}")
print(f"Skipped: {skipped_count}")

input("\nPress Enter to exit...")
