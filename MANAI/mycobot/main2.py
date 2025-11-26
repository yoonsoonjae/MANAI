import cv2
import mediapipe as mp
import socket
import time
import math
from collections import deque
from flask import Flask, Response
import threading



PC2_IP = "192.168.211.243" 
UDP_PORT = 5051            
SEND_INTERVAL = 1.0         

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


cap = cv2.VideoCapture(0, cv2.CAP_MSMF)

mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    model_complexity=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)


J1_RANGE = 90.0
J1_DEADZONE = 0.05

def calc_j1(lm):
    xs = [p.x for p in lm]
    x_mean = sum(xs)/len(xs)
    norm = (x_mean - 0.5) * 2
    if abs(norm) < J1_DEADZONE:
        norm = 0
    return max(-1, min(1, norm)) * J1_RANGE

def calc_pitch(lm, top=0.2, bottom=0.8):
    y = lm[0].y
    y = max(top, min(bottom, y))
    return -90 * (1 - (y - top) / (bottom - top))

def calc_normal(i, p, w):
    Ax, Ay, Az = i.x - w.x, i.y - w.y, i.z - w.z
    Bx, By, Bz = p.x - w.x, p.y - w.y, p.z - w.z
    return (Ay*Bz - Az*By, Az*Bx - Ax*Bz, Ax*By - Ay*Bx)

def wrist_pitch(n):
    nx, ny, nz = n
    pitch = math.degrees(math.atan2(abs(ny), math.sqrt(nx*nx + nz*nz)))
    return max(0, min(90, 90 - pitch))

def map_j4(w):
    j4 = (2*w - 150) / 2
    return max(-40, min(40, j4))

def robot_map(j, p, j4):
    p = max(-90, min(0, p))
    n = (p + 90) / 90
    j2 = max(0, min(35, n * 35))
    j3 = max(0, min(60, n * 60))
    return -j, -j2, -j3, j4


GRIP_OPEN = 100  
GRIP_CLOSE = 0

def is_fist(lm):

    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    count = 0
    for t, p in zip(tips, pips):
        if lm[t].y > lm[p].y:
            count += 1
    return (count >= 3)


def send_robot_udp(j1, j2, j3, j4, grip):
    msg = f"{int(j1)},{int(j2)},{int(j3)},{int(j4)},{grip}"
    sock.sendto(msg.encode(), (PC2_IP, UDP_PORT))
    print("[PC1 SEND]", msg)


latest_frame = None

def process_loop():
    global latest_frame
    bufJ1, bufP, bufW = deque(maxlen=30), deque(maxlen=30), deque(maxlen=30)
    last_send = time.time()

    while True:
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)
        if not ret:
            continue

        latest_frame = frame.copy()

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            lm = result.multi_hand_landmarks[0].landmark
            j1 = calc_j1(lm)
            p  = calc_pitch(lm)
            w  = wrist_pitch(calc_normal(lm[5], lm[17], lm[0]))
            j4 = map_j4(w)
            grip = GRIP_CLOSE if is_fist(lm) else GRIP_OPEN

            bufJ1.append(j1)
            bufP.append(p)
            bufW.append(j4)

            now = time.time()
            if now - last_send >= SEND_INTERVAL:
                J1 = sum(bufJ1)/len(bufJ1)
                P  = sum(bufP)/len(bufP)
                W  = sum(bufW)/len(bufW)
                rj1, rj2, rj3, rj4 = robot_map(J1, P, W)
                send_robot_udp(rj1, rj2, rj3, rj4, grip)
                bufJ1.clear(); bufP.clear(); bufW.clear()
                last_send = now

            mp_draw.draw_landmarks(frame, result.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS)

        cv2.imshow("PC1 Hand Debug", frame)
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


app = Flask(__name__)

def gen_mycam():
    while True:
        if latest_frame is None:
            continue
        _, jpg = cv2.imencode('.jpg', latest_frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' +
               jpg.tobytes() + b'\r\n')

@app.route("/mycam")
def mycam():
    return Response(gen_mycam(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    t = threading.Thread(target=process_loop, daemon=True)
    t.start()
    print("[PC1] Flask Stream on http://localhost:5000/mycam")
    app.run(host="0.0.0.0", port=5000, debug=False)
