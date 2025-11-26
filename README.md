MediaPipe Hands로 사람의 손동작을 인식하고, **UDP 통신을 통해 PC2 → Arduino → myCobot 280** 로봇팔을 조종하는 시스템입니다. 또한 PC1에서 촬영한 영상은 Flask 서버를 통해 **실시간 스트리밍(URL: `/mycam`)** 으로 제공되어 PC2에서도 동일한 화면을 보며 제어할 수 있습니다.

## 🔧 **시스템 구성**

| 구성 | 설명 |
| --- | --- |
| PC1 | 손동작 인식 + UDP 로봇 제어 명령 송신 + Flask 영상 스트리밍 |
| PC2 | PC1 영상 수신 + 로봇 제어 명령 수신 후 Arduino로 전달 |
| 로봇 | myCobot 280 for Arduino |

## 🎮 **제어 방식**

| 조작 | 동작 |
| --- | --- |
| 손 위치(X축) | 로봇 J1 회전 |
| 손 높이(Y축) | 로봇 팔(어깨/팔꿈치) 상승/하강 |
| 손바닥 기울기(법선 벡터) | 손목 Pitch → J4 |
| 주먹 쥠 | 그리퍼 닫기 |
| 손 펴기 | 그리퍼 열기 |

## 📷 **Flask 실시간 스트리밍**

PC1의 웹캠 영상은 다음 주소에서 스트리밍됩니다:

```
http://localhost:5000/mycam

```

## main2.py **실행 방법**

### 1) Python Requirements

```bash
pip install opencv-python mediapipe flask

```

### 2) 코드 실행

```bash
python main2.py
```

실행 시 출력:

```
[PC1] Flask Stream on http://localhost:5000/mycam

```

### 🎯 손 Landmark 기반 계산

| 기능 | 사용 Landmark |
| --- | --- |
| 손 위치(X) → J1 | 모든 Landmark 평균 X |
| 팔 Pitch | 손목 Y 좌표 |
| 노멀 벡터 계산 | Index MCP(5), Pinky MCP(17), Wrist(0) |
| 주먹 감지 | Tip(8,12,16,20) / PIP 비교 |
