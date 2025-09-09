import subprocess

from multiprocessing import Process, Event
from search_ip_connect import *
from open_frame import *
from logging_prog import *


def open_cam_detect(camera_info, students, session_id):
    """
    Main function to handle multiple cameras (IP cameras and webcams).

    Args:
        camera_info: Dictionary containing camera information and stop event
        students: List of students (for future face recognition)
        session_id: Session identifier
    """
    stop_event = camera_info.get("stop_event")  # Event to stop all cameras

    if not camera_info.get("list_cam"):
        logger.info("No cameras found in this room.")
        return

    processes = []
    network_scanned = False
    mac_to_ip = {}

    for cam in camera_info["list_cam"]:
        cam_type = cam.get("type")  # "ipcam" or "webcam"

        if not cam_type:
            logger.warning(f"Skipping camera entry with missing type: {cam}")
            continue

        if cam_type == "ipcam":
            # Handle IP Camera
            mac_address = cam.get("mac")
            username = cam.get("username")
            password = cam.get("password")

            if not all([mac_address, username, password]):
                logger.warning(f"Skipping IP camera (missing mac/credentials): {cam}")
                continue

            # Scan network only once (only when we find first ip camera)
            if not network_scanned:
                devices = scan_all_devices()
                mac_to_ip = {dev["mac"].lower(): dev["ip"] for dev in devices}
                network_scanned = True

            ip = mac_to_ip.get(mac_address.lower())
            if ip:
                logger.info(f"Opening IP camera MAC {mac_address} at IP {ip}")

                # Create camera config for IP camera
                camera_config = {
                    "type": "ipcam",
                    "ip": ip,
                    "username": username,
                    "password": password,

                }

                p = Process(
                    target=open_camera_stream,
                    args=(camera_config, stop_event, session_id),
                )
                p.start()
                processes.append(p)
            else:
                logger.warning(f"MAC {mac_address} not found on the network.")

        elif cam_type == "webcam":
            # Handle Webcam - using 'mac' field as device path
            device_path = cam.get("mac")  # e.g., "/dev/video1"

            if not device_path:
                logger.warning(f"Skipping webcam (missing device path in 'mac' field): {cam}")
                continue

            logger.info(f"Opening webcam '{cam.get('name', 'Unknown')}' at {device_path}")

            # Create camera config for webcam
            camera_config = {
                "type": "webcam",

            }

            # Check if device_path is a string path or numeric ID
            if isinstance(device_path, str) and device_path.startswith("/dev/video"):
                camera_config["device_path"] = device_path
            else:
                # Try to convert to integer for device ID
                try:
                    camera_config["device_id"] = int(device_path)
                except (ValueError, TypeError):
                    camera_config["device_path"] = device_path

            p = Process(
                target=open_camera_stream,
                args=(camera_config, stop_event, session_id),
            )
            p.start()
            processes.append(p)

        else:
            logger.warning(f"Unknown camera type {cam_type} for camera ")

    return processes


def run_post_treatment(token,session_id):
    print(f" Launching recognition as subprocess for session {session_id}")

    # Use the Python inside your virtual environment !!!!!!!
    venv_python = "/home/khalil/Desktop/server/academie_attendance_system/.venv/bin/python"
    script_path = "/home/khalil/Desktop/server/academie_attendance_system/classification_detection.py"

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