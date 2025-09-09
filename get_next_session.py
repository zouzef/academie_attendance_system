import json
from datetime import datetime
from refresh_token import APIClient
import serial
from time import sleep
import time
from testing_api_compreFace.testing_get_idbyname import subject_name

arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)

USERNAME = "f4:4d:30:ee:c9:1d"
PASSWORD = "4156ac789eaa0dc23d5cfb570a23f950ea9bcc63877b3a78a6a86604892d2d01"
BASE_URL = "https://www.unistudious.com"

OUTPUT_FILE = "next_seance.json"

api = APIClient(BASE_URL)

def save_next_seance(seance):
    """Save next seance to JSON file."""
    with open(OUTPUT_FILE, "w") as f:
        json.dump(seance, f, indent=4, ensure_ascii=False)
def main():

    try:
        api.login(USERNAME, PASSWORD)
        resp = api.request("GET", "/slc/get-next-attendance", verify=False)
        resp.raise_for_status()
        data = resp.json().get("data", [])

        if not data:
            print("⚠️ No seances found.")
            exit()

        # Convert "start" strings to datetime objects
        for s in data:
            s["start_dt"] = datetime.strptime(s["start"], "%Y-%m-%d %H:%M:%S")
        # Sort by start time

        data = sorted(data, key=lambda x: x["start_dt"])
        # Loop through consecutive seances

        for i in range(len(data) - 1):
            current = data[i]["start_dt"]
            next_s = data[i + 1]["start_dt"]
            #print("\n",data[i])
            diff_hours = (next_s - current).total_seconds() / 3600
            if diff_hours>=7:
                time_str = next_s.strftime("%H:%M")
                print(time_str)# e.g., "14:30"
                arduino.write(f"{time_str}\n".encode())
                print("the time is registred in the eprom of the cart ")
            if abs(diff_hours - 7) < 0.01:  # ≈ 7 hours
                print(f"✅ Found match: {data[i+1]['name']} at {next_s}")
                save_next_seance({
                    "id": data[i+1]["id"],
                    "name": data[i+1]["name"],
                    "start": data[i+1]["start"],
                    "end": data[i+1]["end"],
                    "subject": data[i+1]["subjectName"]
                })
                break
        else:
            print("ℹ️ No séance with 7-hour gap found.")
    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    main()