from function_api import *
from function_main_file import *
from detection_function import *
from download_files import *
import time
from datetime import datetime, timedelta
import os
import urllib3
from logging_prog import logger








urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
compreface_api_key = "6251a868-7a9e-4fd3-996f-02ffa4210636"
compreface_url = "http://localhost:8000"

def main():

    if(login_as_slc()):
        now = datetime.now()
        logger.info(f"connected at {now.strftime('%H:%M:%S')}")

        status = "up"
        requests.post(
            "https://127.0.0.1:5000/api/server-report",
            json={"status": status},  # Use json, not data
            verify=False  # ← ignore certificate verification
        )

        started_sessions = []  # Already started sessions
        active_sessions = []  # Track sessions with detection processes
        token2=login_as_slc()
        while True:
            try:



                calender = get_all_calendars(token2)

                now = datetime.now()
                print(f"\n Checking at {now.strftime('%H:%M:%S')}")
                sessions_soon = []
                sessions_later = []
                for session in calender['data']:
                    start_time_str = session.get('start')
                    session_id = session.get('id')
                    room_id = session.get('roomId')

                    if not start_time_str or not session_id:
                        continue

                    try:
                        start_time = datetime.fromisoformat(start_time_str)
                    except Exception:
                        logger.error(f" Could not parse start time for session {session_id}: {start_time_str}")

                        continue

                    time_to_start = (start_time - now).total_seconds()

                    if 0 < time_to_start <= 900:  # Session starts in next 15 min
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

                if sessions_soon:
                    print("\n Sessions starting within 15 minutes:")
                    for s in sessions_soon:
                        if s['id'] in started_sessions:
                            continue


                        face_crops_dir, full_frames_dir, pkl_dir = create_dataset_folders(s['id'])
                        session_folder = os.path.join("dataset", f"session_{s['id']}")  # main session folder

                        list_student = get_list_students(s, token2)
                        list_camera = get_all_camera(token2, s['roomId'])

                        # Pass session_folder to save images inside the session folder
                        session_folder = os.path.join("dataset", f"session_{s['id']}")
                        create_dataset_folders(s['id'])

                        # Define img_known folder inside session folder
                        img_known_folder = os.path.join(session_folder, "img_known")
                        os.makedirs(img_known_folder, exist_ok=True)
                        os.chmod(img_known_folder, 0o777)

                        # Pass this to your image download function
                        get_all_img_file(list_student, token2,save_dir=img_known_folder)

                        detection_processes = start_detection_for_session(
                            s['id'], s['roomId'], list_student, list_camera
                        )

                        started_sessions.append(s['id'])
                        active_sessions.append({
                            "session_id": s['id'],
                            "end_time": s['startTime'] + timedelta(minutes=1),
                            "processes": detection_processes
                        })
                else:
                    print("\n No sessions starting within the next 15 minutes.")

                # -------- Stop sessions after 15 minutes --------
                now = datetime.now()

                for session in active_sessions[:]:
                    if now >= session['end_time']:
                        print(f" Stopping detection for session {session['session_id']}")
                        for proc_info in session['processes']:
                            proc_info["stop_event"].set()  # Tell the stream to stop
                            proc_info["process"].join()  # Wait for it to close

                        # Post-detection processing (treatment)
                        try:
                            print(f" Running post-treatment for session {session['session_id']}")
                            run_post_treatment(session['session_id'], token2)
                        except Exception as treatment_error:
                            print(f" Error in post-treatment for session {session['session_id']}: {treatment_error}")

                        active_sessions.remove(session)

                # -------- Display future sessions --------
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
                status_server_load = "down"
                requests.post(
                    "https://127.0.0.1:5000/api/server-load-report",
                    json={"status": status_server_load,"erreur":str(e)},  # Use json, not data
                    verify=False  # ← ignore certificate verification
                )
                print("❌ Error:", e)
                break
    else:
        logger.error(f"❌ Error connextion to server ")
        status="down"
        requests.post(
            "https://127.0.0.1:5000/api/server-report",
            json={"status": status,"Erruer":"unauthorized"},  # Use json, not data
            verify=False  # ← ignore certificate verification
        )
        print("Status sent:", status)

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.set_start_method('spawn')  # ← ADD THIS LINE
    main()
