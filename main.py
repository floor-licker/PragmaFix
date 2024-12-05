import os
import re
import git
import shutil  # For deleting the directory
from config import UN, PW  # Import username and PAT from config.py

# Define the current solidity version to enforce
CURRENT_SOLIDITY_VERSION = "^0.8.0"
SAFE_MATH_IMPORT_PATTERN = re.compile(r"import\s+['\"].*SafeMath.*['\"]\s*;")
SAFE_MATH_USAGE_PATTERN = re.compile(r"\.add\(|\.sub\(|\.mul\(|\.div\(|\.mod\(")
BRANCH_NAME = "pragma-safeMath-refactor"  # Branch name reflecting pragma updates and SafeMath refactoring

def is_using_safe_math(file_path):
    """Check if SafeMath is being used in the Solidity file (either through 'using SafeMath' or imports)."""
    with open(file_path, "r") as file:
        content = file.read()

    # Check for 'using SafeMath' declaration or imports from SafeMath
    if "using SafeMath" in content or "import" in content and "SafeMath" in content:
        return True
    return False

def update_solidity_file(file_path, repo):
    with open(file_path, "r") as file:
        content = file.readlines()

    updated_content = []
    pragma_updated = False  # Tracks if pragma was updated
    safe_math_removed = False  # Tracks if SafeMath was removed

    # Check if the file is using SafeMath
    uses_safe_math = is_using_safe_math(file_path)

    for line in content:
        # Update pragma if it's outdated (only for versions lower than ^0.8.0)
        if line.strip().startswith("pragma solidity"):
            # Match pragma lines with versions lower than ^0.8.0
            if re.match(r"pragma solidity [<|=|>]*[0-7].*", line.strip()):
                updated_content.append(f"pragma solidity {CURRENT_SOLIDITY_VERSION};\n")
                pragma_updated = True
            else:
                updated_content.append(line)
        # Remove SafeMath import if SafeMath is used
        elif SAFE_MATH_IMPORT_PATTERN.search(line) and uses_safe_math:
            safe_math_removed = True
        else:
            # If SafeMath is used, replace SafeMath usages with native operators
            if uses_safe_math and SAFE_MATH_USAGE_PATTERN.search(line):
                line = re.sub(r"\.add\(", " + (", line)
                line = re.sub(r"\.sub\(", " - (", line)
                line = re.sub(r"\.mul\(", " * (", line)
                line = re.sub(r"\.div\(", " / (", line)
                line = re.sub(r"\.mod\(", " % (", line)
                safe_math_removed = True
            updated_content.append(line)

    # If changes were made, save, stage, commit, and push the file
    if pragma_updated or safe_math_removed:
        with open(file_path, "w") as file:
            file.writelines(updated_content)
        print(f"updated: {file_path}")

        # Stage the file using relative path
        rel_path = os.path.relpath(file_path, repo.working_dir)
        print(f"staging file: {rel_path}")
        repo.git.add(rel_path)

        # Generate a descriptive commit message
        changes = []
        if pragma_updated:
            changes.append("updated pragma")
        if safe_math_removed:
            changes.append("removed SafeMath")
        commit_message = f"update {rel_path}: {', '.join(changes)}"

        # Commit the file
        repo.index.commit(commit_message)
        print(f"committed changes: {commit_message}")

        # If this is the first time pushing the branch, set the upstream
        if repo.git.rev_parse("--abbrev-ref", "HEAD") == BRANCH_NAME:
            repo.git.push("--set-upstream", "origin", BRANCH_NAME)
        else:
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

def clone_and_update_repo(repo_url):
    # Define the temporary local directory
    local_dir = "temp_local_repo"

    # Add authentication to the repo URL using username and PAT
    if "https://" in repo_url:
        auth_repo_url = repo_url.replace("https://", f"https://{UN}:{PW}@")
    else:
        auth_repo_url = repo_url  # Use the URL as is (e.g., for SSH)

    try:
        # Clone the repository
        print(f"Cloning repository: {auth_repo_url}")
        repo = git.Repo.clone_from(auth_repo_url, local_dir)

        # Fetch all remote branches
        repo.git.fetch()

        # Check if the branch exists, and create it if not
        if BRANCH_NAME not in [branch.name for branch in repo.branches]:
            print(f"Branch '{BRANCH_NAME}' does not exist. Creating it.")
            # Create and switch to the new branch from the current HEAD
            repo.git.checkout('HEAD', b=BRANCH_NAME)
        else:
            print(f"Switching to branch '{BRANCH_NAME}'.")
            repo.git.checkout(BRANCH_NAME)

        # Process the directory to update Solidity files
        print(f"Processing directory: {local_dir}")
        process_directory(local_dir, repo)

    finally:
        # Clean up the local directory after the script finishes
        print(f"Cleaning up: deleting {local_dir}")
        shutil.rmtree(local_dir, ignore_errors=True)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Update Solidity files in a GitHub repository.")
    parser.add_argument("repo_url", type=str, help="URL of the GitHub repository.")
    args = parser.parse_args()

    clone_and_update_repo(args.repo_url)
