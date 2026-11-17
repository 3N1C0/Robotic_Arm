# Robotic Arm: Kinematics Simulator and JARVIS Controller

This project has two parts. The first is a 4-DOF desktop robotic arm with 3D-printed parts (`STL_files/`). The second is software for it: an interactive web app that visualises forward and inverse kinematics, and a control backend that links a web interface and speech input to an Arduino over serial.

**Live kinematics app:** https://dof-kinematics-simulation.streamlit.app/

## What's inside

| Path | What it is |
|---|---|
| `app.py` | Streamlit app: forward and inverse kinematics for 2- and 3-link planar arms, with plots |
| `STL_files/` | 3D-printable parts for the arm |
| `Code_files/Jarvis_Backend.py` | Flask-SocketIO server that bridges the web UI, speech recognition and serial |
| `Code_files/Jarvis_Frontend.html` | Browser control panel for the backend |
| `Code_files/Jarvis_Arduino.ino` | Arduino firmware that receives commands over serial |
| `test.ipynb` | Notebook used for experiments |

## Skills demonstrated

- **Robotics maths:** forward kinematics (joint angles to end-effector position) and inverse kinematics (target position to joint angles) for planar linkages.
- **Interactive visualisation:** Streamlit sidebars for link lengths, Plotly plots that update on input.
- **Real-time systems:** WebSocket communication with Flask-SocketIO.
- **Embedded integration:** serial communication with `pyserial`, with a port picker and connection handling.
- **Mechanical design:** the arm's parts were modelled in CAD and exported as STL.

## Run the kinematics app

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Run the JARVIS backend

```bash
pip install flask flask-socketio pyserial speechrecognition eventlet
python Code_files/Jarvis_Backend.py
```

Upload `Code_files/Jarvis_Arduino.ino` to the Arduino first, then connect the backend to its serial port from the web page.

## Notes

- The backend's `SECRET_KEY` is a development placeholder. Change it before exposing the server to any network.
- The arm's control code is still in progress.
