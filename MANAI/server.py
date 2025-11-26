import cv2
import socket
import serial
import time
import threading
from flask import Flask, Response


UDP_PORT = 5051            
ARDUINO_PORT = "COM7"
ARDUINO_BAUD = 9600
CAM_INDEX = 1               


print("[PC2] Arduino 연결 중...")
ser = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)
time.sleep(2)
print("[PC2] Arduino Connected:", ARDUINO_PORT)


app = Flask(__name__)

cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_MSMF)
print(f"[PC2] Using CAM index: {CAM_INDEX}")

def gen():
    while True:
        ret, frame = cap.read()
        if not ret: continue
        _, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' +
               jpg.tobytes() + b'\r\n')

@app.route("/cam")
def cam():
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")



last_grip = None 

def udp_loop():
    global last_grip
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", UDP_PORT))
    print(f"[PC2] UDP 서버 시작 (포트 {UDP_PORT})")

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            vals = data.decode().strip().split(",")
            if len(vals) != 5:
                print("[PC2 ERR] wrong format:", vals)
                continue

            j1, j2, j3, j4, grip = vals


            angle_cmd = f"ANGLE:{j1},{j2},{j3},{j4},0,0\n"
            ser.write(angle_cmd.encode())
            print("[PC2 → Arduino]", angle_cmd.strip())


            if grip != last_grip:
                grip_cmd = f"GRIP:{grip}\n"
                ser.write(grip_cmd.encode())
                print("[PC2 → Arduino]", grip_cmd.strip())
                last_grip = grip

        except Exception as e:
            print("[PC2 UDP ERROR]", e)
            time.sleep(0.3)


if __name__ == "__main__":
    threading.Thread(target=udp_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8000, debug=False)
