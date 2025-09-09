import face_recognition
from ultralytics import YOLO
import cv2
import os
import time
import threading
from datetime import datetime
import torch
from insightface.app import FaceAnalysis
import numpy as np
from logging_prog import *
from test import *


# Check CUDA availability
USE_CUDA = torch.cuda.is_available()
#print(f"CUDA available: {USE_CUDA}")

# Load YOLO face detection model
model_path = "best.pt"



def create_dataset_folders(session_id):
    """
    Create dataset folder structure for a specific session.
    Creates:
      dataset/session_{session_id}/
      dataset/session_{session_id}/pkl_files/
      dataset/session_{session_id}/face_crops/
      dataset/session_{session_id}/all_frames/
    """
    main_dir = os.path.join("dataset", f"session_{session_id}")
    pkl_dir = os.path.join(main_dir, "pkl_files")
    face_crops_dir = os.path.join(main_dir, "face_crops")
    full_frames_dir = os.path.join(main_dir, "all_frames")

    try:
        os.makedirs(pkl_dir, exist_ok=True)
        os.chmod(pkl_dir, 0o777)
        os.makedirs(face_crops_dir, exist_ok=True)
        os.chmod(face_crops_dir, 0o777)
        os.makedirs(full_frames_dir, exist_ok=True)
        os.chmod(full_frames_dir, 0o777)
        # Also set permissions for the main session directory
        os.chmod(main_dir, 0o777)
        print(f"✅ Created folders for session {session_id}")
        return face_crops_dir, full_frames_dir, pkl_dir
    except Exception as e:
        logger.error(f"❌ Error creating folders for session {session_id}: {e}")
        return None, None, None


def open_camera_stream(camera_config, stop_event, session_id, max_images_per_person=20):
    """
    Universal camera stream function that works with both IP cameras and webcams.

    Args:
        camera_config: Dictionary containing camera configuration
                      For IP camera: {"type": "ipcam", "ip": "192.168.1.100", "username": "user", "password": "pass"}
                      For webcam: {"type": "webcam", "device_path": "/dev/video0"} or {"type": "webcam", "device_id": 0}
        stop_event: Event to signal stopping
        session_id: Session identifier for folder creation
        max_images_per_person: Maximum images to save per detected face
    """
    # === Setup ===
    # Check CUDA availability and compatibility
    USE_CUDA = False
    if torch.cuda.is_available():
        try:
            # Test CUDA compatibility by creating a small tensor
            test_tensor = torch.zeros(1).cuda()
            del test_tensor
            USE_CUDA = True
            logger.info("🧠 CUDA is available and compatible")
        except Exception as e:
            logger.warning(f"⚠️ CUDA available but incompatible: {e}")
            logger.info("🧠 Falling back to CPU processing")
            USE_CUDA = False
    else:
        logger.info("🧠 CUDA not available, using CPU")

    logger.info(f"🧠 Starting camera stream with face detection (CUDA: {USE_CUDA})...")

    # Load YOLOv8 model with error handling
    try:
        model = YOLO(model_path)
        if USE_CUDA:
            model = model.to('cuda')
        else:
            model = model.to('cpu')
    except Exception as e:
        logger.error(f"❌ Failed to load YOLO model: {e}")
        if USE_CUDA:
            logger.info("🔄 Retrying with CPU...")
            try:
                model = YOLO(model_path).to('cpu')
                USE_CUDA = False
            except Exception as cpu_e:
                logger.error(f"❌ Failed to load model on CPU too: {cpu_e}")
                return
        else:
            return

    # Create folders first
    face_crops_dir, full_frames_dir, pkl_dir = create_dataset_folders(session_id)

    if not face_crops_dir or not full_frames_dir or not pkl_dir:
        logger.error("❌ Failed to create folders. Exiting...")
        return

    # Store known face encodings and counts
    known_faces = []
    face_counts = []

    # Determine camera type and create appropriate capture source
    cam_type = camera_config.get("type")

    if cam_type == "ipcam":
        # IP Camera setup
        ip = camera_config.get("ip")
        username = camera_config.get("username")
        password = camera_config.get("password")

        if not all([ip, username, password]):
            logger.error("❌ Missing IP camera credentials. Exiting...")
            return

        capture_source = f"rtsp://{username}:{password}@{ip}:554/Stream1"
        capture_backend = cv2.CAP_FFMPEG
        logger.info(f"📡 Connecting to IP camera: {capture_source}")

        # Set FFMPEG options for RTSP
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

    elif cam_type == "webcam":
        # Webcam setup
        device_path = camera_config.get("device_path")
        device_id = camera_config.get("device_id")

        if device_path:
            capture_source = device_path
        elif device_id is not None:
            capture_source = device_id
        else:
            logger.error("❌ Missing webcam device path or ID. Exiting...")
            return

        capture_backend = cv2.CAP_V4L2 if device_path else cv2.CAP_ANY
        logger.info(f"📷 Connecting to webcam: {capture_source}")

    else:
        logger.error(f"❌ Unknown camera type: {cam_type}. Exiting...")
        return

    while not stop_event.is_set():
        # Create video capture object
        if cam_type == "ipcam":
            cap = cv2.VideoCapture(capture_source, capture_backend)
            # Set buffer size to reduce latency for IP cameras
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            # Set frame resolution (adjust based on camera capabilities)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        else:
            # Webcam
            cap = cv2.VideoCapture(capture_source, capture_backend)
            # Set webcam properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)

        if not cap.isOpened():
            error_msg = f"❌ Failed to open {cam_type}: {capture_source}. "
            if cam_type == "ipcam":
                error_msg += "Retrying in 5 seconds..."
                print(error_msg)
                time.sleep(5)
                continue  # Try to reconnect for IP cameras
            else:
                error_msg += "Exiting..."
                print(error_msg)
                return  # Exit for webcams

        logger.info(f"✅ Connected to {cam_type}: {capture_source}")
        print("🔍 Running face detection and recognition...")

        frame_count = 0
        PADDING_PERCENT = 0.20

        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                if cam_type == "ipcam":
                    break  # Break inner loop to reconnect
                else:
                    cap.release()
                    cv2.destroyAllWindows()
                    return  # Exit for webcams

            # Run detection with error handling
            try:
                results = model.predict(source=frame, show=False, conf=0.4, device='cuda' if USE_CUDA else 'cpu')
            except Exception as e:
                logger.error(f"❌ YOLO prediction failed: {e}")
                if USE_CUDA:
                    logger.info("🔄 Retrying with CPU...")
                    try:
                        model = model.to('cpu')
                        USE_CUDA = False
                        results = model.predict(source=frame, show=False, conf=0.4, device='cpu')
                    except Exception as cpu_e:
                        logger.error(f"❌ CPU prediction also failed: {cpu_e}")
                        continue
                else:
                    continue

            for box in results[0].boxes:
                conf = float(box.conf[0])
                if conf < 0.70:
                    continue

                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

                # Calculate padding based on face size
                width = x2 - x1
                height = y2 - y1
                x_pad = int(width * PADDING_PERCENT)
                y_pad = int(height * PADDING_PERCENT)

                # Apply padding (ensure we don't go outside the image boundaries)
                h, w = frame.shape[:2]
                x1 = max(0, x1 - x_pad)
                y1 = max(0, y1 - y_pad)
                x2 = min(w, x2 + x_pad)
                y2 = min(h, y2 + y_pad)

                # Draw box (now with padding)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{conf:.2f}", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # Crop face (now with padding)
                face_crop = frame[y1:y2, x1:x2]
                if face_crop.size == 0:
                    continue

                # Save image with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
                face_filename = f"face_{timestamp}.jpg"
                frame_filename = f"frame_{timestamp}.jpg"

                is_good_quality, quality_score = check_face_quality(face_crop, quality_threshold=0.60)

                if is_good_quality:
                    # Save image with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
                    face_filename = f"face_{timestamp}.jpg"
                    frame_filename = f"frame_{timestamp}.jpg"

                    cv2.imwrite(os.path.join(face_crops_dir, face_filename), face_crop, [cv2.IMWRITE_JPEG_QUALITY, 100])
                    cv2.imwrite(os.path.join(full_frames_dir, frame_filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 100])

                    print(f"✅ Saved face (quality: {quality_score:.3f}): {face_filename}")
                    print(f"✅ Saved full frame: {frame_filename}")
                else:
                    print(f"❌ Skipped low quality face (score: {quality_score:.3f})")

                break  # Save only one face per frame

            # Show frame
            #cv2.imshow(f"Face Detection - {cam_type.upper()}", frame)
            #if cv2.waitKey(1) & 0xFF == ord('q'):
            #    print("🛑 'q' pressed. Stopping stream...")
            #    stop_event.set()  # Signal to stop outer loop
            #    break

        cap.release()  # Release capture before reconnect or exit

    #cv2.destroyAllWindows()
    #print("🛑 Stream stopped cleanly.")