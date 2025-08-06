import requests
from logging_prog import logger


BASEURL="https://www.unistudious.com"
CALENDAR_URL=f"{BASEURL}/slc/get-all-calendar"


api_key="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3NTMwODkwMDksImV4cCI6MTc1MzY5MzgwOSwicm9sZXMiOlsiUk9MRV9TTEMiXSwidXNlcm5hbWUiOiJjYzoyODphYTo4Njo1Mzo5NyJ9.EQXaHDrAkPjcslJ6IrR883KAWgoqztnoRYewhtF5S2GXVGmQVqLNRdGe3U-f7j3Japo-j6LUUmV3NRz41uucTW5-xq_fmtbOUw-YqtXZF2iyV2NiVOaQv-_ouL2kqZ403U5XPay9mECxbUgADMViiWRO_ln01pKUhUNU2rMvcAmQr6Q-NCvGHAjjWQcdpRg3-Y4EfO9YY5zmUAyi4UDHxevlRTCb7h9AGlu-mx536v-WxeRRB_j6dlJYviUMQIxwBaFeva81AuYF6bnNF-Vy9pSwK-90YWbKIv0RkSBhPdJ1OCnYsEijKt_7fzyD-Qr-efguAQLQ6nOvmc_9-l7jFg"

def get_all_attendence(attendance_id,token):
    try:
        ATTENDANCE_URL = f"{BASEURL}/slc/get-attendance/{attendance_id}"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.post(ATTENDANCE_URL, headers=headers)
        response.raise_for_status()
        data = response.json()

        payload = {
            "id": attendance_id
        }

        response = requests.post(ATTENDANCE_URL, headers=headers, data=payload)
        response.raise_for_status()
        data = response.json()
        return data['attendance']
    except Exception as e:
        logger.error(f"Error getting attendance: {e}")




def update_status(student_id,token,etat):
    try:
        UPDATE_ATTENDANCE_URL=f"{BASEURL}/slc/update-attendance-student/{student_id}"
        headers={
            "Authorization": f"Bearer {token}"
        }
        payload={
            "status":bool(etat)
        }

        response=requests.post(UPDATE_ATTENDANCE_URL,headers=headers,data=payload)
        response.raise_for_status()
        data=response.json()
        return data
    except Exception as e:
        logger.error(f"Error updating status: {e}")


def get_id(id,list_student):

    for i in list_student:

        if i['userId']==id:
            return i['id']


def update_all_list_present(list_present,id_attendance,token):

    attendance_list=get_all_attendence(id_attendance,token)

    try:
        for userId,percent in list_present:
            id=get_id(userId,attendance_list)
            print(id)
            update_status(id,token,True)



        logger.info("update all list present with succes")

    except Exception as e:
        logger.error(f"Error updating status: {e}")


