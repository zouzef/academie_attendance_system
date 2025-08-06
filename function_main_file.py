import os
from logging_prog import *
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