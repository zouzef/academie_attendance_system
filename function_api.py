import requests
from logging_prog import logger
payload = {
    "username": "cc:28:aa:86:53:97",
    "password": "e6cae0c2392f5bf3d609c9abe7e1589c8860b4375b8e775cf62046dc09bb29d7",
}



API_URL = "https://www.unistudious.com/api_slc/login_check"
CALENDAR_URL = "https://www.unistudious.com/slc/get-all-calendar"



def login_as_slc():


    try:

        response = requests.post(API_URL, json=payload)

        print(" Server Response Code:", response.status_code)
        token2 = response.json().get("token")
        print(token2)
        if token2 is not None:
            return token2
    except Exception as e:
        logger.error(f"❌ Error in login_as_slc: {str(e)}")
        return None,e


# Function to get all the students of the session
def get_list_students(l, token):
    try:
        list_students_session = []
        calendar_id = l['id']
        url = f"https://www.unistudious.com/slc/get-attendance/{calendar_id}"
        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.post(url, headers=headers)
        response.raise_for_status()

        # ✅ Convert response to JSON
        data = response.json()

        # ✅ Extract student attendance
        if 'attendance' in data:
            for j in data['attendance']:
                student = {
                    'id': j.get('id'),
                    'userName': j.get('userName'),
                    'userId': j.get('userId'),
                    'userRefRlc': j.get('userRefRlc'),
                    'isPresent': j.get('isPresent')
                }
                list_students_session.append(student)


        else:
            logger.info("❌ 'attendance' key not found in response:", data)


        return list_students_session

    except Exception as e:
        logger.error(f"❌ Error in login_as_slc: {str(e)}")








def list_students_wid(id_attendance, token):
    list_students_session = []
    url = f"https://www.unistudious.com/slc/get-attendance/{id_attendance}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()

        # ✅ Convert response to JSON
        data = response.json()

        # ✅ Extract student attendance
        if 'attendance' in data:
            for j in data['attendance']:
                student = {
                    'id': j.get('id'),
                    'userName': j.get('userName'),
                    'userId': j.get('userId'),
                    'userRefRlc': j.get('userRefRlc'),
                    'isPresent': j.get('isPresent')
                }
                list_students_session.append(student)


        else:
            logger.info("❌ 'attendance' key not found in response:", data)


        return list_students_session
    except Exception as e:
        logger.error(f"❌ Error in login_as_slc: {str(e)}")




def get_all_camera(token: str, room_id: int):
    try:
        url = f"https://www.unistudious.com/slc/get-all-camera-room/{room_id}"
        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()

        cameras = []

        if isinstance(data, list):  # if the response is a list of camera dicts
            for cam in data:
                camera = {
                    "id": cam.get("id"),
                    "name": cam.get("name"),
                    "mac": cam.get("mac"),
                    "username": cam.get("username"),
                    "password": cam.get("password"),
                    "status": cam.get("status"),
                    "roomId": cam.get("roomId"),
                    "roomName": cam.get("roomName"),
                    "created_at": cam.get("created_at")
                }
                cameras.append(camera)
        else:
            logger.info(f"Unexpected format from camera API: {data}")


        return cameras

    except Exception as e:
        logger.error(f"❌ Error in login_as_slc: {str(e)}")



def get_all_calendars(token: str):

    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(CALENDAR_URL, headers=headers)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        logger.error(f"❌ Error in get_all_calendars: {str(e)}")

