import requests
from logging_prog import logger


BASEURL="https://www.unistudious.com"
CALENDAR_URL=f"{BASEURL}/slc/get-all-calendar"


def get_all_attendence(attendance_id, token):
    try:
        ATTENDANCE_URL = f"{BASEURL}/slc/get-attendance/{attendance_id}"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(ATTENDANCE_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get('attendance', [])
    except Exception as e:
        logger.error(f"Error getting attendance: {e}")
        return []


def update_status(student_id, token, etat):
    try:
        url = f"{BASEURL}/slc/update-attendance-student/{student_id}"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"status": bool(etat)}
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return response.status_code
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        return None


def update_all_list_present(list_present,id_attendance,token):
    try:
        for userId,percent in list_present:
            if(update_status(userId,token,True)):
                logger.info(f"update student{userId} present with succes")
        logger.info(f"update student{id_attendance} present with succes")
    except Exception as e:

        logger.error(f"Error updating status: {e}")