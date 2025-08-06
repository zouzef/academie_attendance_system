import os
import requests
from logging_prog import *
BASE_URL = "https://www.unistudious.com"


def create_cloud_folder(calendar_id, image_path, token):
    try:
        url = f"{BASE_URL}/slc/set-unknown-attendance-student-folder/{calendar_id}"
        headers = {"Authorization": f"Bearer {token}"}

        with open(image_path, "rb") as f:
            files = {"file": f}
            response = requests.post(url, headers=headers, files=files)

        response.raise_for_status()
        data = response.json()

        return data.get("id")
    except Exception as e:
        logging.error(f"Error cloud:{e}")


def upload_image_to_folder(folder_id, image_path, token):
    url = f"{BASE_URL}/slc/set-unknown-attendance-student-file/{folder_id}"
    headers = {"Authorization": f"Bearer {token}"}

    with open(image_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, headers=headers, files=files)

    response.raise_for_status()



def process_all_person_folders(classified_unknown, token, session_id):
    if not os.path.exists(classified_unknown):
        logger.error(f"❌ Folder not found: {classified_unknown}")
        return

    for person_folder in os.listdir(classified_unknown):
        if person_folder == "unknown_person":
            continue  # skip that folder

        person_path = os.path.join(classified_unknown, person_folder)

        if os.path.isdir(person_path):
            images = sorted([
                f for f in os.listdir(person_path)
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))
            ])

            if not images:
                continue

            first_image_path = os.path.join(person_path, images[0])


            folder_id = create_cloud_folder(session_id, first_image_path, token)

            if not folder_id:
                print(f"❌ Failed to create folder for {person_folder}")
                continue

            for image_name in images[1:]:
                image_path = os.path.join(person_path, image_name)
                upload_image_to_folder(folder_id, image_path, token)

