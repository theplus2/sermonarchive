import os
import re
import subprocess
import sys
from datetime import datetime

def get_current_version(app_path):
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'page_title="설교자의 서재 (v\d+\.\d+\.\d+)"', content)
    if match:
        return match.group(1)
    return None

def update_app_version(app_path, old_version, new_version):
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content.replace(old_version, new_version)
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated {app_path} version from {old_version} to {new_version}")

def update_changelog(changelog_path, new_version, log_content):
    date_str = datetime.now().strftime("%Y-%m-%d")
    header = f"## [{new_version}] - {date_str}\n"
    entry = f"{header}\n{log_content}\n\n"
    
    if os.path.exists(changelog_path):
        with open(changelog_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        new_content = entry + existing_content
    else:
        new_content = "# Changelog\n\n" + entry
        
    with open(changelog_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated {changelog_path}")

def run_git_commands(new_version):
    commands = [
        ["git", "add", "."],
        ["git", "commit", "-m", f"Release {new_version}"],
        ["git", "tag", new_version],
        ["git", "push", "origin", "main"],
        ["git", "push", "origin", new_version]
    ]
    
    for cmd in commands:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            # 태그가 이미 존재하거나 하는 경우 등 에러 처리
            if "tag" in cmd and "already exists" in result.stderr:
                 print("Tag already exists, skipping tag creation.")
            else:
                 sys.exit(1)
        else:
            print(result.stdout)

import argparse

def main():
    parser = argparse.ArgumentParser(description="Release Helper Script")
    parser.add_argument("--version", help="New version (e.g., v5.3.0)")
    parser.add_argument("--log", help="Update log message")
    parser.add_argument("-y", "--yes", action="store_true", help="Auto-confirm git operations")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(base_dir, "app.py")
    docs_dir = os.path.join(base_dir, "docs")
    changelog_path = os.path.join(docs_dir, "release_log_v5.1.md") # CHANGELOG.md was used in previous code, but user has release_log files. Let's stick to creating a generic CHANGELOG.md or appending to a new one. The user has release_log_v5.1.md. I'll create CHANGELOG.md if not exists logic is already there.

    # Wait, the previous code used "release_log_v5.1.md" in my mind but wrote to CHANGELOG.md in code?
    # Let's check the code I wrote in Step 70.
    # It wrote to os.path.join(docs_dir, "CHANGELOG.md")
    # I should stick to that or create a new log file.
    changelog_path = os.path.join(docs_dir, "CHANGELOG.md")
    
    current_version = get_current_version(app_path)
    if not current_version:
        print("Could not find current version in app.py")
        sys.exit(1)
        
    print(f"Current version: {current_version}")
    
    if args.version:
        new_version = args.version
    else:
        new_version = input(f"Enter new version (e.g., v5.3.0): ").strip()
    
    if not new_version:
        print("Version cannot be empty.")
        sys.exit(1)
    
    if args.log:
        log_content = args.log
    else:
        print("Enter update log (Press Enter twice to finish):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        log_content = "\n".join(lines)
    
    update_app_version(app_path, current_version, new_version)
    update_changelog(changelog_path, new_version, log_content)
    
    if args.yes:
        confirm = 'y'
    else:
        confirm = input("Proceed with git commit and push? (y/n): ").lower()
        
    if confirm == 'y':
        run_git_commands(new_version)
    else:
        print("Aborted git operations.")

if __name__ == "__main__":
    main()
