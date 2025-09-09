from logging_prog import logger

# ============================
# GET ALL CALENDARS
# ============================
def get_all_calendars(api):
    """Fetch all calendar entries."""
    try:
        resp = api.request("GET", "/slc/get-all-calendar", verify=False)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"❌ Error in get_all_calendars: {e}")
        return {}

# ============================
# GET STUDENTS OF A SESSION
# ============================
def get_list_students(api, session):
    """Fetch student attendance list for a given session."""
    try:
        url = f"/slc/get-attendance/{session['id']}"
        resp = api.request("POST", url, verify=False)
        resp.raise_for_status()
        data = resp.json()

        students = []
        if 'attendance' in data:
            for j in data['attendance']:
                students.append({
                    'id': j.get('id'),
                    'userName': j.get('userName'),
                    'userId': j.get('userId'),
                    'userRefRlc': j.get('userRefRlc'),
                    'isPresent': j.get('isPresent')
                })
        else:
            logger.warning(f"⚠️ 'attendance' not found in response: {data}")
        return students

    except Exception as e:
        logger.error(f"❌ Error in get_list_students: {e}")
        return []

# ============================
# GET STUDENTS BY ATTENDANCE ID
# ============================
def list_students_wid(api, id_attendance):
    """Fetch students for a given attendance ID."""
    try:
        url = f"/slc/get-attendance/{id_attendance}"
        resp = api.request("POST", url, verify=False)
        resp.raise_for_status()
        data = resp.json()

        students = []
        if 'attendance' in data:
            for j in data['attendance']:
                students.append({
                    'id': j.get('id'),
                    'userName': j.get('userName'),
                    'userId': j.get('userId'),
                    'userRefRlc': j.get('userRefRlc'),
                    'isPresent': j.get('isPresent')
                })
        else:
            logger.warning(f"⚠️ 'attendance' not found in response: {data}")
        return students

    except Exception as e:
        logger.error(f"❌ Error in list_students_wid: {e}")
        return []

# ============================
# GET CAMERAS IN A ROOM
# ============================
def get_all_camera(api, room_id: int):
    """Fetch all cameras in a specific room."""
    try:
        url = f"/slc/get-all-camera-room/{room_id}"
        resp = api.request("GET", url, verify=False)
        resp.raise_for_status()
        data = resp.json()

        cameras = []
        if isinstance(data, list):
            for cam in data:
                cameras.append({
                    "id": cam.get("id"),
                    "type": cam.get("type"),
                    "name": cam.get("name"),
                    "mac": cam.get("mac"),
                    "username": cam.get("username"),
                    "password": cam.get("password"),
                    "status": cam.get("status"),
                    "roomId": cam.get("roomId"),
                    "roomName": cam.get("roomName"),
                    "created_at": cam.get("created_at")
                })
        else:
            logger.warning(f"⚠️ Unexpected camera API format: {data}")
        return cameras

    except Exception as e:
        logger.error(f"❌ Error in get_all_camera: {e}")
        return []