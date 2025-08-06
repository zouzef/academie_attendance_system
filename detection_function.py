import subprocess
from multiprocessing import Process
from multiprocessing import Process, Event
from search_ip_connect import *
from open_frame import *
from logging_prog import *

def open_cam_detect(camera_info,students,session_id):
    stop_event = camera_info.get("stop_event")  # Get the stop_event from parent process

    if not camera_info.get('list_cam'):
        logger.info("No cameras found in this room.")
        return

    devices = scan_all_devices()
    mac_to_ip = {dev['mac'].lower(): dev['ip'] for dev in devices}

    processes = []
    for cam in camera_info['list_cam']:
        mac = cam.get('mac')
        username = cam.get('username')
        password = cam.get('password')
        if not mac or not username or not password:
            logger.info(f"Skipping camera with missing MAC/username/password: {cam}")
            continue
        ip = mac_to_ip.get(mac.lower())
        if ip:
            logger.info(f"Opening stream for camera MAC {mac} at IP {ip} with user {username}")
            # Pass stop_event as argument
            p = Process(target=open_rtsp_stream, args=(ip, username, password, stop_event,session_id))
            p.start()
            processes.append(p)
        else:
            logger.info(f"MAC {mac} not found on the network.")


def run_post_treatment(session_id,token):
    print(f" Launching recognition as subprocess for session {session_id}")

    # Use the Python inside your virtual environment
    venv_python = "/home/kernelsipc/PycharmProjects/academie_attendance/.venv/bin/python"


    script_path = "/home/kernelsipc/PycharmProjects/academie_attendance/main_progrmme/classification_detection.py"

    subprocess.Popen([venv_python, script_path, str(session_id), token])




def start_detection_for_session(session_id, room_id, students, cameras):
    logger.info(f"🎬 Starting detection for session {session_id} in room {room_id}...")

    stop_event = Event()

    camera_info = {
        "list_cam": cameras,
        "students": students,
        "stop_event": stop_event
    }



    process = Process(target=open_cam_detect, args=(camera_info,students,session_id))
    process.start()

    return [{
        "process": process,
        "stop_event": stop_event
    }]