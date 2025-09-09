import os
import shutil
import requests
import zipfile
import json
from packaging import version

# CONFIGURABLE
GITHUB_REPO = "zouzef/academie_attendance_system"
LOCAL_VERSION_FILE = "version.json"  # Path to local version.json
DOWNLOAD_DIR = "latest_update"
EXCLUDE = ["update_checker.py", DOWNLOAD_DIR]  # Files/folders NOT to delete#yousef test

def get_remote_version():
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/version.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("❌ Failed to fetch remote version:", e)
        return None

def get_local_version():
    if not os.path.exists(LOCAL_VERSION_FILE):
        print("⚠️ Local version.json not found.")
        return None
    with open(LOCAL_VERSION_FILE) as f:
        return json.load(f)

def download_latest_zip():
    url = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/main.zip"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    zip_path = os.path.join(DOWNLOAD_DIR, "latest.zip")
    print("⬇️ Downloading latest version...")
    try:
        response = requests.get(url, stream=True)
        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("✅ Download complete.")
        return zip_path
    except Exception as e:
        print("❌ Download failed:", e)
        return None

def extract_zip(zip_path):
    print("📦 Extracting new version...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(DOWNLOAD_DIR)
    print("✅ Extraction done.")


def delete_old_files():
    print("🧹 Removing old version files...")
    for item in os.listdir("."):
        if item in EXCLUDE:
            continue
        try:
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)
        except Exception as e:
            print(f"❌ Failed to delete {item}: {e}")
    print("✅ Old files removed.")

def replace_with_new_version():
    extracted_folder = os.path.join(DOWNLOAD_DIR, f"{GITHUB_REPO.split('/')[1]}-main")
    for item in os.listdir(extracted_folder):
        src = os.path.join(extracted_folder, item)
        dest = os.path.join(".", item)
        try:
            if os.path.isdir(src):
                shutil.copytree(src, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dest)
        except Exception as e:
            print(f"❌ Failed to copy {item}: {e}")
    print("🚀 Updated to new version.")


def main():
    print("🔎 Checking for updates...")
    remote_data = get_remote_version()
    local_data = get_local_version()
    if not remote_data or not local_data:
        print("⚠️ Could not read version data.")
        return
    if not remote_data.get("stable", False):
        print("⚠️ Remote version is not marked as stable. Skipping update.")
        return
    remote_ver = version.parse(remote_data["version"])
    local_ver = version.parse(local_data["version"])
    if remote_ver > local_ver:
        print(f"⬆️ New version available: {remote_ver} (current: {local_ver})")
        zip_path = download_latest_zip()
        if zip_path:
            extract_zip(zip_path)
            delete_old_files()
            replace_with_new_version()
            print("✅ Update complete. Please restart the application.")
    else:
        print("✅ Already up to date.")

if __name__ == "__main__":
    main()
