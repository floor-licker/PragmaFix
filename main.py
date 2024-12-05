import os
import re
import git

# define the current solidity version to enforce
CURRENT_SOLIDITY_VERSION = "^0.8.0"
SAFE_MATH_IMPORT_PATTERN = re.compile(r"import\s+['\"].*SafeMath.*['\"]\s*;")
SAFE_MATH_USAGE_PATTERN = re.compile(r"\.add\(|\.sub\(|\.mul\(|\.div\(|\.mod\(")

def update_solidity_file(file_path, repo):
    with open(file_path, "r") as file:
        content = file.readlines()

    updated_content = []
    changes_made = False  # Tracks if any changes are made to the file

    for line in content:
        # Update pragma if it's outdated
        if line.strip().startswith("pragma solidity"):
            if line.strip() != f"pragma solidity {CURRENT_SOLIDITY_VERSION};":
                updated_content.append(f"pragma solidity {CURRENT_SOLIDITY_VERSION};\n")
                changes_made = True
            else:
                updated_content.append(line)
        # Remove SafeMath import
        elif SAFE_MATH_IMPORT_PATTERN.search(line):
            changes_made = True
        else:
            # Replace SafeMath usages with native operators
            if SAFE_MATH_USAGE_PATTERN.search(line):
                line = re.sub(r"\.add\(", "+(", line)
                line = re.sub(r"\.sub\(", "-(", line)
                line = re.sub(r"\.mul\(", "*(", line)
                line = re.sub(r"\.div\(", "/(", line)
                line = re.sub(r"\.mod\(", "%(", line)
                changes_made = True
            updated_content.append(line)

    # If changes were made, save, stage, commit, and push the file
    if changes_made:
        with open(file_path, "w") as file:
            file.writelines(updated_content)
        print(f"updated: {file_path}")

        # Stage the file using relative path
        rel_path = os.path.relpath(file_path, repo.working_dir)
        print(f"staging file: {rel_path}")
        repo.git.add(rel_path)

        # Commit the file
        commit_message = f"update {rel_path}: updated pragma and removed safemath"
        repo.index.commit(commit_message)
        print(f"committed changes: {commit_message}")

        # Push the commit
        repo.git.push()
        print(f"pushed changes for: {rel_path}")
    else:
        print(f"no changes needed: {file_path}")

def process_directory(directory, repo):
    # Process each Solidity file in the directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".sol"):
                file_path = os.path.join(root, file)
                update_solidity_file(file_path, repo)

def clone_and_update_repo(repo_url, local_dir):
    # Clone the repository
    print(f"cloning repository: {repo_url}")
    if os.path.exists(local_dir):
        print(f"directory '{local_dir}' already exists. skipping clone.")
        repo = git.Repo(local_dir)  # Open the existing repository
    else:
        repo = git.Repo.clone_from(repo_url, local_dir)

    # Process the directory to update Solidity files
    print(f"processing directory: {local_dir}")
    process_directory(local_dir, repo)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="update solidity files in a github repository.")
    parser.add_argument("repo_url", type=str, help="url of the github repository.")
    parser.add_argument("local_dir", type=str, help="local directory to clone the repository into.")
    args = parser.parse_args()

    clone_and_update_repo(args.repo_url, args.local_dir)

