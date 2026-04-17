"""
JARVIS Web Backend — Flask-SocketIO + Serial Bridge
====================================================
Runs a local web server that:
  1. Serves the JARVIS dashboard (index.html)
  2. Accepts voice audio from the browser via WebSocket
  3. Transcribes speech → matches commands → sends to Arduino
  4. Pushes Arduino acknowledgements back to the browser in real time

Requirements:
    pip install flask flask-socketio pyserial speechrecognition eventlet

Usage:
    python app.py
    Then open http://localhost:5001 in your browser.
"""

import os
import io
import sys
import time
import queue
import threading
import tempfile
import concurrent.futures
import serial
import serial.tools.list_ports
import speech_recognition as sr
from pydub import AudioSegment

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit

# ─── App Setup ────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config["SECRET_KEY"] = "jarvis-secret-key"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# Thread pool for non-blocking STT processing — 4 workers handles concurrent requests
executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

# ─── Command Table ────────────────────────────────────────────────────────────
# Format: "spoken keyword": ("SERIAL_CMD", "JARVIS response text")
# Longer phrases are matched first — "turn left" always beats "left"

COMMANDS = {
    # Wave
    "wave":           ("WAVE",      "Initiating greeting wave sequence."),
    "greet":          ("WAVE",      "Greeting sequence engaged."),
    "hello":          ("WAVE",      "Hello. Raising arm and waving."),
    "say hello":      ("WAVE",      "Salutations. Executing wave."),

    # Spin
    "spin":           ("SPIN",      "Performing a full base sweep."),
    "rotate":         ("SPIN",      "Rotating. Full sweep in progress."),
    "sweep":          ("SPIN",      "Sweeping the base. Stand clear."),

    # Dance
    "dance":          ("DANCE",     "Engaging full choreography routine. Shall we dance?"),
    "perform":        ("DANCE",     "Performance sequence initiated."),
    "show off":       ("DANCE",     "Displaying full range of motion. Watch closely."),

    # Salute
    "salute":         ("SALUTE",    "Presenting arms. Executing military salute."),
    "attention":      ("SALUTE",    "Snapping to attention. Salute engaged."),
    "yes sir":        ("SALUTE",    "Sir. Executing salute immediately."),

    # Stretch
    "stretch":        ("STRETCH",   "Initiating full range of motion calibration stretch."),
    "calibrate":      ("STRETCH",   "Calibrating. Sweeping all joints through full range."),
    "warm up":        ("STRETCH",   "Warming up all joints. Full stretch in progress."),

    # Shake
    "shake":          ("SHAKE",     "Executing rapid wrist shake sequence."),
    "no":             ("SHAKE",     "Negative. Shaking in disagreement."),
    "disagree":       ("SHAKE",     "I disagree. Demonstrating with a firm shake."),

    # Reach
    "reach":          ("REACH",     "Extending arm outward. Reach sequence initiated."),
    "extend":         ("REACH",     "Extending to full reach. Stand by."),
    "grab":           ("REACH",     "Reach and retract sequence engaged."),

    # Point
    "point":          ("POINT",     "Pointing and scanning. Eyes front."),
    "look":           ("POINT",     "Directing your attention. Pointing now."),
    "there":          ("POINT",     "Confirmed. Pointing at the target."),

    # Celebrate
    "celebrate":      ("CELEBRATE", "Victory confirmed. Initiating celebration sequence."),
    "yes":            ("CELEBRATE", "Excellent. Celebrating your success."),
    "good job":       ("CELEBRATE", "Outstanding work. Victory celebration engaged."),

    # Rest
    "rest":           ("REST",      "Returning arm to rest position. Standing by."),
    "stop":           ("REST",      "Stopping all movement. Returning to rest."),
    "reset":          ("REST",      "Resetting to default rest position."),
    "stand down":     ("REST",      "Standing down. All joints returning to rest."),
}

# ─── Serial Manager ───────────────────────────────────────────────────────────

class SerialManager:
    """
    Singleton serial worker.
    - Runs a background thread that drains the command queue and reads Arduino ACKs.
    - Only one process owns the port at a time.
    - Handles reconnection automatically on port loss.
    """

    def __init__(self):
        self.conn        = None
        self.port        = None
        self.connected   = False
        self.cmd_queue   = queue.Queue()
        self._lock       = threading.Lock()
        self._stop_event = threading.Event()
        self._thread     = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    # ── Port Discovery ──────────────────────────────────────────────────────

    def list_ports(self):
        return [
            {"device": p.device, "description": p.description}
            for p in serial.tools.list_ports.comports()
        ]

    def connect(self, port, baud=9600):
        """Open the serial port. Returns (True, msg) or (False, error)."""
        with self._lock:
            if self.conn and self.conn.is_open:
                self.conn.close()
            try:
                self.conn      = serial.Serial(port=port, baudrate=baud, timeout=1)
                self.port      = port
                self.connected = True
                time.sleep(2)  # Wait for Arduino reboot
                self._broadcast_status("connected", f"Connected to {port}")
                return True, f"Connected to {port}"
            except serial.SerialException as e:
                self.connected = False
                self._broadcast_status("error", str(e))
                return False, str(e)

    def disconnect(self):
        with self._lock:
            if self.conn and self.conn.is_open:
                self.send_command("REST")   # Safe park before disconnect
                time.sleep(0.5)
                self.conn.close()
            self.connected = False
            self._broadcast_status("disconnected", "Serial port closed.")

    # ── Command Queue ───────────────────────────────────────────────────────

    def send_command(self, cmd):
        """Queue a command string for serial transmission."""
        self.cmd_queue.put(cmd)

    # ── Background Worker ───────────────────────────────────────────────────

    def _worker(self):
        """Drain the command queue and listen for Arduino ACKs."""
        while not self._stop_event.is_set():
            # --- Send queued commands ---
            try:
                cmd = self.cmd_queue.get_nowait()
                if self.conn and self.conn.is_open:
                    try:
                        with self._lock:
                            self.conn.write(f"{cmd}\n".encode("utf-8"))
                        print(f"[Serial] Sent: {cmd}")
                    except serial.SerialException as e:
                        print(f"[Serial] Write error: {e}")
                        self.connected = False
                        self._broadcast_status("error", f"Write failed: {e}")
            except queue.Empty:
                pass

            # --- Read Arduino ACKs ---
            try:
                if self.conn and self.conn.is_open and self.conn.in_waiting:
                    line = self.conn.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        print(f"[Arduino] {line}")
                        socketio.emit("arduino_ack", {"message": line})
            except serial.SerialException as e:
                print(f"[Serial] Read error: {e}")
                self.connected = False
                self._broadcast_status("error", f"Connection lost: {e}")

            time.sleep(0.05)

    def _broadcast_status(self, status, message):
        socketio.emit("serial_status", {"status": status, "message": message})

    def stop(self):
        self._stop_event.set()
        if self.conn and self.conn.is_open:
            self.conn.close()


serial_mgr = SerialManager()

# ─── Command Matching ─────────────────────────────────────────────────────────

def match_command(text):
    """Match transcribed text to a command. Longest phrase wins."""
    sorted_cmds = sorted(COMMANDS.items(), key=lambda x: len(x[0]), reverse=True)
    for keyword, (cmd, response) in sorted_cmds:
        if keyword in text:
            return cmd, response
    return None, None

# ─── Audio Conversion ─────────────────────────────────────────────────────────

def convert_to_wav(audio_bytes):
    """
    Convert browser audio (WebM/OGG) to 16kHz mono WAV.
    16kHz mono is the optimal format for Google STT —
    smaller file size and faster processing than raw browser audio.
    """
    raw     = io.BytesIO(bytes(audio_bytes))
    seg     = AudioSegment.from_file(raw)
    seg     = seg.set_frame_rate(16000).set_channels(1)
    wav_io  = io.BytesIO()
    seg.export(wav_io, format="wav")
    wav_io.seek(0)
    return wav_io

# ─── STT Worker (runs in thread pool) ────────────────────────────────────────

def process_voice(audio_bytes, sid):
    """
    Runs off the main SocketIO thread via ThreadPoolExecutor.
    Converts audio → transcribes → matches command → emits result.
    """
    recognizer = sr.Recognizer()
    try:
        wav_io = convert_to_wav(audio_bytes)

        with sr.AudioFile(wav_io) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio).lower()
        print(f"[STT] Heard: '{text}'")

        cmd, response = match_command(text)
        if cmd:
            serial_mgr.send_command(cmd)
            socketio.emit("command_result", {
                "heard":    text,
                "command":  cmd,
                "response": response,
                "success":  True
            }, to=sid)
        else:
            socketio.emit("command_result", {
                "heard":    text,
                "command":  None,
                "response": f"I heard '{text}' but it didn't match any command.",
                "success":  False
            }, to=sid)

    except sr.UnknownValueError:
        socketio.emit("command_result", {
            "heard": "", "command": None,
            "response": "Could not understand audio.", "success": False
        }, to=sid)
    except sr.RequestError as e:
        socketio.emit("command_result", {
            "heard": "", "command": None,
            "response": f"STT service error: {e}", "success": False
        }, to=sid)
    except Exception as e:
        print(f"[Voice Error] {e}")
        socketio.emit("command_result", {
            "heard": "", "command": None,
            "response": f"Audio processing error: {e}", "success": False
        }, to=sid)

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ports")
def ports():
    return jsonify(serial_mgr.list_ports())

# ─── WebSocket Events ─────────────────────────────────────────────────────────

@socketio.on("connect")
def on_connect():
    status = "connected" if serial_mgr.connected else "disconnected"
    emit("serial_status", {
        "status": status,
        "message": "JARVIS online. Awaiting your command." if serial_mgr.connected
                   else "No Arduino connected. Select a port to begin."
    })

@socketio.on("connect_serial")
def on_connect_serial(data):
    port = data.get("port")
    baud = data.get("baud", 9600)
    if not port:
        emit("serial_status", {"status": "error", "message": "No port specified."})
        return
    success, msg = serial_mgr.connect(port, baud)
    emit("serial_status", {"status": "connected" if success else "error", "message": msg})

@socketio.on("disconnect_serial")
def on_disconnect_serial():
    serial_mgr.disconnect()

@socketio.on("button_command")
def on_button_command(data):
    """Handle direct button press from UI — no voice needed."""
    cmd = data.get("command", "").upper()
    if cmd in [c for c, _ in COMMANDS.values()]:
        response = next((r for _, (c, r) in COMMANDS.items() if c == cmd), "Command sent.")
        serial_mgr.send_command(cmd)
        emit("command_result", {
            "heard":    f"[Button] {cmd}",
            "command":  cmd,
            "response": response,
            "success":  True
        })
    else:
        emit("command_result", {"heard": cmd, "command": None, "response": "Unknown command.", "success": False})

@socketio.on("voice_audio")
def on_voice_audio(data):
    """
    Receive audio from browser, hand off to thread pool immediately.
    The SocketIO thread is freed instantly — no blocking on STT.
    """
    audio_bytes = data.get("audio")
    if not audio_bytes:
        emit("command_result", {"heard": "", "command": None, "response": "No audio received.", "success": False})
        return
    sid = request.sid
    executor.submit(process_voice, audio_bytes, sid)

@socketio.on("text_command")
def on_text_command(data):
    """Handle typed text command from UI."""
    text = data.get("text", "").lower().strip()
    cmd, response = match_command(text)
    if cmd:
        serial_mgr.send_command(cmd)
        emit("command_result", {
            "heard":    text,
            "command":  cmd,
            "response": response,
            "success":  True
        })
    else:
        emit("command_result", {
            "heard":    text,
            "command":  None,
            "response": f"No command matched for '{text}'.",
            "success":  False
        })

# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  J.A.R.V.I.S. Web Server — Starting up")
    print("  Open http://localhost:5001 in your browser")
    print("=" * 55)
    try:
        socketio.run(app, host="0.0.0.0", port=5001, debug=False)
    except KeyboardInterrupt:
        print("\n[Exit] Shutting down JARVIS.")
        serial_mgr.stop()
        sys.exit(0)
