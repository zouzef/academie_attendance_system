import json
import os
import subprocess

VERSION_FILE = "version.json"

def init_version_file():
    version_data = {
        "version": "1.0.0",
        "stable": True,
        "changelog": "Initial release"
    }
    with open(VERSION_FILE, "w") as f:
        json.dump(version_data, f, indent=4)
    print("Initialized version.json with version 1.0.0")
    return version_data

def load_version():
    if not os.path.exists(VERSION_FILE):
        return init_version_file()
    with open(VERSION_FILE) as f:
        return json.load(f)

def save_version(version_data):
    with open(VERSION_FILE, "w") as f:
        json.dump(version_data, f, indent=4)

def bump_version(version, bump_type):
    major, minor, patch = map(int, version.split('.'))
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    return f"{major}.{minor}.{patch}"

def git_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print("Git command failed:", e)
        exit(1)

def main():
    print("🚀 Release Manager for Master")

    version_data = load_version()
    current_version = version_data['version']
    print(f"Current version: {current_version}")

    bump_type = input("What type of update? (major/minor/patch): ").strip().lower()
    if bump_type not in ['major', 'minor', 'patch']:
        print("Invalid version bump type.")
        return

    new_version = bump_version(current_version, bump_type)
    changelog = input("Enter changelog: ").strip()

    # Update version.json
    version_data['version'] = new_version
    version_data['stable'] = True
    version_data['changelog'] = changelog
    save_version(version_data)

    print(f"📦 Updated to version {new_version}, committing to Git...")

    # Git commands
    git_command("git add .")
    git_command(f'git commit -m "Release v{new_version}: {changelog}"')
    git_command("git push origin main")

    print("✅ Code pushed successfully to GitHub.")

if __name__ == "__main__":
    main()
