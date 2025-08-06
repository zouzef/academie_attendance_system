import face_recognition
from ultralytics import YOLO
import cv2
import os
import time
import threading
from datetime import datetime
import torch
import numpy as np
from logging_prog import *
# Check CUDA availability
USE_CUDA = torch.cuda.is_available()
print(f"CUDA available: {USE_CUDA}")

# Load YOLO face detection model
model_path = "/home/kernelsipc/PycharmProjects/PythonProject/OIDv4_ToolKit/runs/detect/pedestrian-detector/weights/best.pt"



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


def open_rtsp_stream(ip, username, password, stop_event,session_id, max_images_per_person=20):
    """
    Opens RTSP stream with integrated YOLO face detection, face recognition,
    and saves crops/frames with improved quality and limits on images per person.

    Args:
        ip: Camera IP address
        username: RTSP username
        password: RTSP password
        stop_event: Event to signal stopping
        max_images_per_person: Maximum images to save per detected face
    """
    # === Setup ===
    USE_CUDA = torch.cuda.is_available()
    logger.info(f"🧠 Starting RTSP stream with face detection (CUDA: {USE_CUDA})...")

    # Load YOLOv8 model
    model = YOLO(model_path).to('cuda' if USE_CUDA else 'cpu')

    # Create folders first
    face_crops_dir, full_frames_dir, pkl_dir = create_dataset_folders(session_id)

    if not face_crops_dir or not full_frames_dir or not pkl_dir:
        logger.error("❌ Failed to create folders. Exiting...")
        return

    # Store known face encodings and counts
    known_faces = []
    face_counts = []

    rtsp_url = f"rtsp://{username}:{password}@{ip}:554/Stream1"
    print(f"📡 Connecting to: {rtsp_url}")

    # Use FFMPEG backend for better RTSP handling
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

    while not stop_event.is_set():
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

        # Set buffer size to reduce latency
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # Set frame resolution (adjust based on camera capabilities)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        if not cap.isOpened():
            print(f"❌ Failed to open stream: {rtsp_url}. Retrying in 5 seconds...")
            time.sleep(5)
            continue  # Try to reconnect

        logger.info(f"✅ Connected to {rtsp_url}")
        print("🔍 Running face detection and recognition...")

        frame_count = 0
        PADDING_PERCENT = 0.199

        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break

            # Run detection
            results = model.predict(source=frame, show=False, conf=0.4, device='cuda' if USE_CUDA else 'cpu')

            for box in results[0].boxes:
                conf = float(box.conf[0])
                if conf < 0.4:
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
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                face_filename = f"face_{timestamp}.jpg"
                frame_filename = f"frame_{timestamp}.jpg"

                cv2.imwrite(os.path.join(face_crops_dir, face_filename), face_crop, [cv2.IMWRITE_JPEG_QUALITY, 100])
                cv2.imwrite(os.path.join(full_frames_dir, frame_filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 100])

                print(f"✅ Saved face: {face_filename}")
                print(f"✅ Saved full frame: {frame_filename}")
                break  # Save only one face per frame

            # Show frame
            cv2.imshow("Face Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("🛑 'q' pressed. Stopping stream...")
                stop_event.set()  # Signal to stop outer loop
                break

        cap.release()  # Release capture before reconnect or exit

    cv2.destroyAllWindows()
    print("🛑 Stream stopped cleanly.")


    print("🛑 Stopping stream gracefully...")
