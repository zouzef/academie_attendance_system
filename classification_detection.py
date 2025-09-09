import os
import requests
import shutil
from classification import *
from sending_folders_to_cloud import *
from change_status import *

COMPRE_FACE_URL = "http://localhost:8000"  # Adjust if needed
THRESHOLD = 0.90  # Similarity threshold

API_KEY = "7488544f-e3e0-43ab-a4f1-a86eb01eba2d"



def recognition_job(session_id, token, students=None):
    print(f"🧠 Launching recognition via CompreFace for session {session_id}")
    print(token)
    base_session_dir = f"./dataset/session_{session_id}"
    session_folder = os.path.join(base_session_dir, "face_crops")
    unknown_dir = None  # Initialize unknown_dir to prevent UnboundLocalError

    if not os.path.exists(session_folder):
        print(f"❌ No folder found for session {session_id}: {session_folder}")
        return

    image_files = [f for f in os.listdir(session_folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not image_files:
        print(f"❌ No image files found in: {session_folder}")
        return

    print(f"✅ Found {len(image_files)} image(s) to process in session {session_id}.\n")

    list_student_detected = []

    for filename in image_files:
        image_path = os.path.join(session_folder, filename)
        print(f"📷 Processing: {image_path}")

        with open(image_path, "rb") as img_file:
            files = {"file": img_file}
            headers = {"x-api-key": API_KEY}
            response = requests.post(
                f"{COMPRE_FACE_URL}/api/v1/recognition/recognize",
                headers=headers,
                files=files
            )

        if response.status_code == 200:

            result = response.json()
            data = result.get("result")
            if data and data[0]["subjects"]:
                subject_name = int(data[0]["subjects"][0]["subject"])
                similarity = data[0]["subjects"][0]["similarity"]

                print(f"👤 Person: {subject_name}")
                print(f"📊 Similarity: {similarity}")

                # Check if subject is already recorded
                if similarity > 0.979 and subject_name not in [name for name, _ in list_student_detected]:
                    list_student_detected.append((subject_name, similarity))
                    print("✅ Match confirmed!")
                elif similarity <0.90:
                    print(f"❌ Low confidence ({similarity}) or already recorded. Moving to unknown.")
                    unknown_dir = os.path.join(session_folder, "unknown_person")
                    os.makedirs(unknown_dir, exist_ok=True)
                    shutil.move(image_path, os.path.join(unknown_dir, filename))
            else:
                print("⚠️ No subject found.")


        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            continue

    print(f"\n✅ Final list of students detected in session {session_id}:")
    print(list_student_detected)

    #this function will change the status of the student apsent/present
    update_all_list_present(list_student_detected,session_id,token)

    #=================================================================#

    #classification of the unkown images
    classified_unknown = os.path.join(session_folder, "classified_unknown")
    classify_faces(unknown_dir, classified_unknown)

    # Upload each classified person folder to cloud
    print("🚀 Uploading classified unknown persons to cloud...")
    process_all_person_folders(classified_unknown,token,session_id)



if __name__ == "__main__":
    import sys

    if len(sys.argv) > 2:
        session_id = sys.argv[1]
        token = sys.argv[2]
        recognition_job(session_id, token)
    else:
        print("❌ Usage: python functions_detection2.py <session_id> <token>")
