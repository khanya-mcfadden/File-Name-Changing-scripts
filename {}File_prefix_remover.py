import os
import re
import sys

# Pattern: Koikatu_F_ + 17 digits + _
pattern = re.compile(r'^Koikatu_F_\d{17}_')

# Use the folder where this script is located
directory = os.path.dirname(os.path.abspath(__file__))

renamed_count = 0
skipped_count = 0

for filename in os.listdir(directory):
    full_path = os.path.join(directory, filename)

    if os.path.isfile(full_path):
        new_name = pattern.sub('', filename)

        if new_name != filename:
            new_path = os.path.join(directory, new_name)

            if not os.path.exists(new_path):
                os.rename(full_path, new_path)
                print(f"Renamed: {filename} -> {new_name}")
                renamed_count += 1
            else:
                print(f"Skipped (already exists): {new_name}")
                skipped_count += 1

print("\nFinished.")
print(f"Renamed: {renamed_count}")
print(f"Skipped: {skipped_count}")

input("\nPress Enter to exit...")
