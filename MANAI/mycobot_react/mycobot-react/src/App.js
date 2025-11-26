
  import "./App.css";

  function App() {
    return (
      <div className="layout">
       
        <div className="cam-area">
          <h2>내 영상 (PC1)</h2>
          <img
            src="http://localhost:5000/mycam"
            alt="my-cam"
            className="cam-view"
          />
        </div>


        <div className="control-area">
          <h2>로봇팔 카메라 (PC2)</h2>
          <img
            src="http://192.168.211.243:8000/cam"
            alt="robot-cam"
            className="cam-view"
          />
        </div>
      </div>
    );
  }

  export default App;
