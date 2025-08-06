import os
import requests
import base64
from logging_prog import *
# === COMPRE-FACE CONFIGURATION ===
COMPRE_FACE_API_KEY = "6251a868-7a9e-4fd3-996f-02ffa4210636"  # Your CompreFace API Key
COMPRE_FACE_HOST = "http://localhost:8000"  # CompreFace base URL
ENROLL_URL = f"{COMPRE_FACE_HOST}/api/v1/recognition/faces"  # Endpoint for enrollment (not collection-based)

# === HEADERS ===
COMPRE_HEADERS = {
    "x-api-key": COMPRE_FACE_API_KEY
}


def upload_image_to_compreface(image_path, subject_label):

    if not os.path.exists(image_path):
        logger.info(f"❌ File does not exist: {image_path}")
        return False

    try:
        with open(image_path, "rb") as f:
            files = {"file": f}
            data = {"subject": subject_label}
            response = requests.post(ENROLL_URL, headers=COMPRE_HEADERS, files=files, data=data)
            response.raise_for_status()
        logger.info(f"✅ Enrolled image '{image_path}' as '{subject_label}'")
        return True
    except requests.exceptions.HTTPError as err:
        logger.info(f"❌ HTTP error while uploading {image_path}: {err}")
        logger.info(f"Response: {response.text}")
    except Exception as e:
        logger.info(f"❌ Failed to upload {image_path}: {e}")
    return False


def download_student_image_base64(token, student_id, save_dir="img_student"):
    """
    Downloads base64 images of student and saves them.

    :param token: Auth token
    :param student_id: Student ID
    :param save_dir: Folder to save to
    :return: List of saved image paths
    """
    url_ref = f"https://www.unistudious.com/slc/get-reference-student/{student_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        ref_response = requests.post(url_ref, headers=headers)
        ref_response.raise_for_status()
        ref_data = ref_response.json()

        file_list = ref_data.get('fileList', [])
        if not file_list:
            logger.info(f"⚠️ No images found for student {student_id}")
            return []

        saved_paths = []
        url_read = "https://www.unistudious.com/slc/google-cloud/read-file"

        for file_path in file_list:
            payload = {"fileName": file_path}
            file_response = requests.post(url_read, headers=headers, json=payload)
            file_response.raise_for_status()
            data = file_response.json()

            b64_content = data.get('content')
            if not b64_content:
                logger.info(f"⚠️ No content found for file {file_path}")
                continue

            image_bytes = base64.b64decode(b64_content)

            os.makedirs(save_dir, exist_ok=True)
            filename = os.path.basename(file_path)
            file_save_path = os.path.join(save_dir, filename)

            with open(file_save_path, 'wb') as f:
                f.write(image_bytes)

            print(f"📥 Saved image: {file_save_path}")
            saved_paths.append(file_save_path)

        return saved_paths

    except Exception as e:
        logger.error(f"❌ Error downloading images for student {student_id}: {e}")
        return []


def get_all_img_file(student_list, token, save_dir="img_dir"):
    """
    Downloads and uploads images for a list of students.

    :param student_list: List of student dicts with userId and userRefRlc
    :param token: Bearer token for API
    :param save_dir: Base folder for saving images
    """
    os.makedirs(save_dir, exist_ok=True)
    os.chmod(save_dir, 0o777)
    count = 0

    for student in student_list:
        if student.get('userRefRlc'):
            student_id = str(student['userId'])
            subject_label = student_id  # Or use a name: f"{student['firstName']} {student['lastName']}"

            student_folder = os.path.join(save_dir, f"{student_id}_imgfolder")
            os.makedirs(student_folder, exist_ok=True)
            os.chmod(student_folder, 0o777)

            saved_images = download_student_image_base64(token, student_id, save_dir=student_folder)

            for img_path in saved_images:
                upload_image_to_compreface(img_path, subject_label)

            count += 1

    logger.info(f"✅ Finished downloading and uploading images for: {count} students")
