import cv2
import mediapipe as mp
import socket
import time
import math
from collections import deque
from flask import Flask, Response
import threading


ROBOT_IP = "192.168.211.243"  
PORT = 5050
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_robot(j1, j2, j3, j4):
    msg = f"{j1:.1f},{j2:.1f},{j3:.1f},{j4:.1f}"
    sock.sendto(msg.encode(), (ROBOT_IP, PORT))
    print("[SEND]", msg)



cap = cv2.VideoCapture(0)
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

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
    if abs(norm) < J1_DEADZONE: norm = 0
    return max(-1,min(1,norm))*J1_RANGE

def calc_pitch(lm,top=0.2,bottom=0.8):
    y = lm[0].y
    y = max(top,min(bottom,y))
    return -90*(1-(y-top)/(bottom-top))

def calc_normal(i,p,w):
    Ax,Ay,Az = i.x-w.x,i.y-w.y,i.z-w.z
    Bx,By,Bz = p.x-w.x,p.y-w.y,p.z-w.z
    return (Ay*Bz-Az*By, Az*Bx-Ax*Bz, Ax*By-Ay*Bx)

def wrist_pitch(n):
    nx,ny,nz=n
    pitch = math.degrees(math.atan2(abs(ny), math.sqrt(nx*nx+nz*nz)))
    return max(0,min(90,90-pitch))

def map_j4(w):
    j4=(2*w-150)/2
    return max(-40,min(40,j4))

def robot_map(j,p,j4):
    p=max(-90,min(0,p)); n=(p+90)/90
    j2=max(0,min(35,n*35))
    j3=max(0,min(60,n*60))
    return -j,-j2,-j3,j4



latest_frame = None

def process_loop():
    global latest_frame
    prev_p,prev_w=None,None
    bufJ1,bufP,bufW=deque(maxlen=30),deque(maxlen=30),deque(maxlen=30)
    last=time.time()

    while True:
        ret, frame = cap.read()
        if not ret: continue
        latest_frame = frame.copy()

        rgb = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        r = hands.process(rgb)

        if r.multi_hand_landmarks:
            lm = r.multi_hand_landmarks[0].landmark
            j1 = calc_j1(lm)
            p = calc_pitch(lm)
            w = wrist_pitch(calc_normal(lm[5],lm[17],lm[0]))
            j4 = map_j4(w)

            bufJ1.append(j1)
            bufP.append(p)
            bufW.append(j4)

            now=time.time()
            if now-last>=1:
                J1=sum(bufJ1)/len(bufJ1)
                P=sum(bufP)/len(bufP)
                W=sum(bufW)/len(bufW)
                send_robot(*robot_map(J1,P,W))
                bufJ1.clear(); bufP.clear(); bufW.clear()
                last=now

            mp_draw.draw_landmarks(frame,r.multi_hand_landmarks[0],mp_hands.HAND_CONNECTIONS)

        cv2.imshow("Angle Debug", frame)
        if cv2.waitKey(1)==27: break

threading.Thread(target=process_loop,daemon=True).start()



app = Flask(__name__)

def gen():
    while True:
        if latest_frame is None: continue
        _, jpg = cv2.imencode('.jpg', latest_frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' +
               jpg.tobytes() + b'\r\n')

@app.route('/mycam')
def mycam():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

app.run(host="0.0.0.0",port=5000,debug=False)
