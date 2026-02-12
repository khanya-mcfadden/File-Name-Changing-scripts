import os
import re

directory = os.path.dirname(os.path.abspath(__file__))

renamed_count = 0
skipped_count = 0

def smart_capitalize(text):
    # Capitalize first letter of each word (letters only)
    return re.sub(r'\b([a-zA-Z])([a-zA-Z]*)',
                  lambda m: m.group(1).upper() + m.group(2).lower(),
                  text)

for filename in os.listdir(directory):
    full_path = os.path.join(directory, filename)

    if os.path.isfile(full_path):
        name, ext = os.path.splitext(filename)

        new_name_part = smart_capitalize(name)
        new_filename = new_name_part + ext

        if new_filename != filename:
            new_path = os.path.join(directory, new_filename)

            # Windows is case-insensitive, so force rename if only case changes
            if os.path.exists(new_path) and new_path.lower() != full_path.lower():
                print(f"Skipped (already exists): {new_filename}")
                skipped_count += 1
            else:
                # Temporary rename if only case difference
                temp_path = full_path + ".temp_rename"
                os.rename(full_path, temp_path)
                os.rename(temp_path, new_path)

                print(f"Renamed: {filename} -> {new_filename}")
                renamed_count += 1

print("\nFinished.")
print(f"Renamed: {renamed_count}")
print(f"Skipped: {skipped_count}")

input("\nPress Enter to exit...")
