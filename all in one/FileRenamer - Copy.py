import os
import re

directory = os.path.dirname(os.path.abspath(__file__))

# ================= SETTINGS =================

MODE = "regex_remove"
# Options:
# "regex_remove"
# "char_remove"
# "add_folder_prefix"

REGEX_PATTERN = r'^Koikatu_F_\d{17}_'
REMOVE_CHAR_COUNT = 28

REMOVE_SPACES_FROM_FOLDER_PREFIX = True

# ============================================


folder_name = os.path.basename(directory)
if REMOVE_SPACES_FROM_FOLDER_PREFIX:
    folder_name = folder_name.replace(" ", "")
FOLDER_PREFIX = folder_name + "_"


renamed_count = 0
skipped_count = 0

for filename in os.listdir(directory):
    full_path = os.path.join(directory, filename)

    if not os.path.isfile(full_path):
        continue

    if filename == os.path.basename(__file__):
        continue

    new_filename = filename

    if MODE == "regex_remove":
        new_filename = re.sub(REGEX_PATTERN, "", filename)

    elif MODE == "char_remove":
        if len(filename) > REMOVE_CHAR_COUNT:
            new_filename = filename[REMOVE_CHAR_COUNT:]

    elif MODE == "add_folder_prefix":
        if not filename.startswith(FOLDER_PREFIX):
            new_filename = FOLDER_PREFIX + filename
        else:
            skipped_count += 1
            print(f"Skipped (already prefixed): {filename}")
            continue

    if new_filename == filename:
        skipped_count += 1
        continue

    new_path = os.path.join(directory, new_filename)

    if os.path.exists(new_path) and new_path.lower() != full_path.lower():
        print(f"Skipped (exists): {new_filename}")
        skipped_count += 1
        continue

    # Windows case-safe rename
    temp_path = full_path + ".tmp_rename"
    os.rename(full_path, temp_path)
    os.rename(temp_path, new_path)

    print(f"Renamed: {filename} -> {new_filename}")
    renamed_count += 1


print("\nFinished")
print("Renamed:", renamed_count)
print("Skipped:", skipped_count)

input("\nPress Enter to exit...")