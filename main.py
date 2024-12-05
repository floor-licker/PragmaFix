import os
import re

# define the current solidity version to update to
CURRENT_SOLIDITY_VERSION = "^0.8.0"
# pattern to find lines that import safemath
SAFE_MATH_IMPORT_PATTERN = re.compile(r"import\s+['\"].*SafeMath.*['\"]\s*;")
# pattern to find safemath methods like .add(), .sub(), etc.
SAFE_MATH_USAGE_PATTERN = re.compile(r"\.add\(|\.sub\(|\.mul\(|\.div\(|\.mod\(")

def update_solidity_file(file_path):
    with open(file_path, "r") as file:
        content = file.readlines()

    updated_content = []
    pragma_updated = False
    safe_math_removed = False

    for line in content:
        # if the line starts with pragma solidity, update it to the current version
        if line.strip().startswith("pragma solidity"):
            updated_content.append(f"pragma solidity {CURRENT_SOLIDITY_VERSION};\n")
            pragma_updated = True
        # if the line imports safemath, skip it
        elif SAFE_MATH_IMPORT_PATTERN.search(line):
            safe_math_removed = True
        else:
            # if the line uses safemath functions, replace them with normal math
            if SAFE_MATH_USAGE_PATTERN.search(line):
                line = re.sub(r"\.add\(", "+(", line)
                line = re.sub(r"\.sub\(", "-(", line)
                line = re.sub(r"\.mul\(", "*(", line)
                line = re.sub(r"\.div\(", "/(", line)
                line = re.sub(r"\.mod\(", "%(", line)
                safe_math_removed = True
            updated_content.append(line)

    # if changes were made, save the file
    if pragma_updated or safe_math_removed:
        with open(file_path, "w") as file:
            file.writelines(updated_content)
        print(f"updated: {file_path}")
    else:
        print(f"no changes needed: {file_path}")

def process_directory(directory):
    # go through all files in the directory and its subdirectories
    for root, _, files in os.walk(directory):
        for file in files:
            # if the file is a solidity file, update it
            if file.endswith(".sol"):
                file_path = os.path.join(root, file)
                update_solidity_file(file_path)

if __name__ == "__main__":
    import argparse

    # set up the script to accept a directory path as input
    parser = argparse.ArgumentParser(description="update solidity files to use the current version and remove safemath.")
    parser.add_argument("directory", type=str, help="path to the folder with solidity files.")
    args = parser.parse_args()

    process_directory(args.directory)
# @floor-licker 2024
