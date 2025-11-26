import { useEffect, useRef } from "react";
import "./App.css";

function App() {
  const myCamRef = useRef(null);

  useEffect(() => {
    // 1번 PC 자체 웹캠 연결
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(stream => {
        if (myCamRef.current) {
          myCamRef.current.srcObject = stream;
        }
      })
      .catch(err => console.error("내 카메라 접근 실패:", err));
  }, []);

  return (
    <div className="layout">
      
      {/* 내 카메라 */}
      <div className="cam-area">
        <h2>내 영상</h2>
        <video
  autoPlay
  muted
  playsInline
  src="192.168.211.243:5000/mycam"
  className="cam-view"
/>

      </div>

      {/* 로봇팔 카메라 (2번 PC) */}
      <div className="control-area">
        <h2>카메라 영상</h2>
        <img
          src="http://192.168.211.243:8000/cam"
          alt="cam"
          className="cam-view"
        />
      </div>

    </div>
  );
}

export default App;
