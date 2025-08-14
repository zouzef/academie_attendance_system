from function_api import *
from function_main_file import *
from detection_function import *
from download_files import *
import time
from datetime import datetime, timedelta
import os
import urllib3
from logging_prog import logger
from refresh_token import APIClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://www.unistudious.com"
USERNAME = "cc:28:aa:86:53:97"# Change to real credentials
PASSWORD = "e6cae0c2392f5bf3d609c9abe7e1589c8860b4375b8e775cf62046dc09bb29d7"


compreface_api_key = "6251a868-7a9e-4fd3-996f-02ffa4210636"
compreface_url = "http://localhost:8000"

def main():
    api = APIClient(BASE_URL)

    # --- LOGIN ---
    try:
        api.login(USERNAME, PASSWORD)
        now = datetime.now()
        logger.info(f"✅ Connected at {now.strftime('%H:%M:%S')}")
        api.request("POST", "/api/server-report", json={"status": "up"}, verify=False)
    except Exception as e:
        logger.error(f"❌ Login failed: {e}")
        api.request(
            "POST",
            "/api/server-report",
            json={"status": "down", "Error": "unauthorized"},
            verify=False
        )
        return

    started_sessions = []
    active_sessions = []
    rooms_without_cameras = set()  # <-- Keep track of rooms with no cameras


    while True:
        try:
            # --- Fetch all calendars --- #
            calender = get_all_calendars(api)  # Updated to use api client inside

            now = datetime.now()
            print(f"\n Checking at {now.strftime('%H:%M:%S')}")
            sessions_soon, sessions_later = [], []

            for session in calender.get("data", []):
                start_time_str = session.get("start")
                session_id = session.get("id")
                room_id = session.get("roomId")

                if not start_time_str or not session_id or room_id in rooms_without_cameras:
                    continue

                try:
                    start_time = datetime.fromisoformat(start_time_str)
                except Exception:
                    logger.error(f" Could not parse start time for session {session_id}: {start_time_str}")
                    continue

                time_to_start = (start_time - now).total_seconds()

                if 0 < time_to_start <= 900:  # within 15 min
                    sessions_soon.append({
                        "id": session_id,
                        "roomId": room_id,
                        "startTime": start_time
                    })
                elif time_to_start > 900:
                    sessions_later.append({
                        "id": session_id,
                        "roomId": room_id,
                        "startTime": start_time
                    })

            # --- Handle sessions starting soon ---
            if sessions_soon:
                print("\n Sessions starting within 15 minutes:")
                for s in sessions_soon:
                    if s["id"] in started_sessions:
                        continue

                    # Get students & cameras
                    list_student = get_list_students(api, s)
                    list_camera = get_all_camera(api, s["roomId"])

                    # Check if there is at least one camera
                    if(len(list_camera)>0):

                        # Create dataset folders
                        face_crops_dir, full_frames_dir, pkl_dir = create_dataset_folders(s["id"])
                        session_folder = os.path.join("dataset", f"session_{s['id']}")
                        os.makedirs(session_folder, exist_ok=True)

                        # Prepare img_known folder
                        img_known_folder = os.path.join(session_folder, "img_known")
                        os.makedirs(img_known_folder, exist_ok=True)
                        os.chmod(img_known_folder, 0o777)

                        # Download known student images
                        get_all_img_file(api, list_student, save_dir=img_known_folder)

                        # Start detection
                        detection_processes = start_detection_for_session(
                            s["id"], s["roomId"], list_student, list_camera
                        )

                        started_sessions.append(s["id"])
                        active_sessions.append({
                            "session_id": s["id"],
                            "end_time": s["startTime"] + timedelta(minutes=1),
                            "processes": detection_processes
                        })
                    else:
                        print("there is no camera in this room ")
                        rooms_without_cameras.add(s["roomId"])
            else:
                print("\n No sessions starting within the next 15 minutes.")

            # --- Stop sessions after 15 minutes ---
            now = datetime.now()
            for session in active_sessions[:]:
                if now >= session["end_time"]:
                    print(f" Stopping detection for session {session['session_id']}")
                    for proc_info in session["processes"]:
                        proc_info["stop_event"].set()
                        proc_info["process"].join()

                    try:
                        print(f" Running post-treatment for session {session['session_id']}")
                        run_post_treatment(api, session["session_id"])
                    except Exception as treatment_error:
                        print(f" Error in post-treatment for session {session['session_id']}: {treatment_error}")

                    active_sessions.remove(session)

            # --- Display future sessions ---
            if sessions_later:
                print("\n Sessions starting later:")
                for s in sessions_later:
                    print(
                        f"  - ID: {s['id']}, Room: {s['roomId']}, Start Time: {s['startTime'].strftime('%H:%M:%S')}")
            else:
                print("\n No upcoming sessions beyond 15 minutes.")

            time.sleep(10)

        except Exception as e:
            logger.error(f"❌ Error Server: {e}")
            api.request(
                "POST",
                "/api/server-load-report",
                json={"status": "down", "erreur": str(e)},
                verify=False
            )
            break

# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.set_start_method("spawn")
    main()
