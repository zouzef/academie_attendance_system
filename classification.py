#change the api keys to get from the dashboard

import os
import requests
import shutil
from logging_prog import *



def classify_faces(input_dir, output_dir, api_key="0e9e5b42-78cd-4623-b488-6ee8871e5931", base_url="http://localhost:8000"):
    VERIFY_ENDPOINT = f"{base_url}/api/v1/verification/verify"
    HEADERS = {"x-api-key": api_key}
    SIMILARITY_THRESHOLD = 0.95  # Adjust if needed

    os.makedirs(output_dir, exist_ok=True)

    def verify(source_path, target_path):
        try:
            files = {
                "source_image": open(source_path, "rb"),
                "target_image": open(target_path, "rb")
            }
            response = requests.post(VERIFY_ENDPOINT, files=files, headers=HEADERS)
            result = response.json()

            # Safety checks
            result_list = result.get("result", [])
            if not result_list or "face_matches" not in result_list[0]:
                print(f"❌ No face match found between:\n   {source_path}\n   {target_path}")
                return False

            face_matches = result_list[0]["face_matches"]
            if not face_matches:
                print(f"❌ Face detected but no similar match found for:\n   {source_path}\n   {target_path}")
                return False

            similarity = face_matches[0].get("similarity", 0)
            threshold = result.get("threshold", 0.95)

            print(f"🔍 Comparing\n   {os.path.basename(source_path)} ↔ {os.path.basename(target_path)}\n   → Similarity: {similarity:.4f} | Threshold: {threshold:.2f}")

            return similarity >= threshold

        except Exception as e:
            logger.error(f"❌ Error comparing images {source_path} and {target_path}: {e}")
            return False

    # Start classification logic
    images = os.listdir(input_dir)
    unprocessed = images.copy()
    group_id = 1

    while unprocessed:
        ref_img = unprocessed.pop(0)
        ref_path = os.path.join(input_dir, ref_img)

        person_folder = os.path.join(output_dir, f"person_{group_id}")
        os.makedirs(person_folder, exist_ok=True)
        shutil.copy(ref_path, os.path.join(person_folder, ref_img))

        matched = []

        for img in unprocessed:
            img_path = os.path.join(input_dir, img)
            if verify(ref_path, img_path):
                shutil.copy(img_path, os.path.join(person_folder, img))

                matched.append(img)

        for m in matched:
            unprocessed.remove(m)

        group_id += 1

    print("✅ Classification complete.")

