from flask import Flask, render_template, send_from_directory, abort
from flask_socketio import SocketIO
from pathlib import Path
import time
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Kamera → katalog bazowy
CAMERA_DIRS = {
    "X1": Path("/ftp/ftp/X1/new_images"),
    "Y1": Path("/ftp/ftp/Y1/new_images"),
}

ALLOWED_EXTS = {".jpg", ".jpeg", ".png"}
MAX_FILES_PER_CATEGORY = 100
last_known = {}

def get_latest_any_and_bad(camera):
    base_dir = CAMERA_DIRS.get(camera)
    if not base_dir or not base_dir.exists():
        return None, []

    latest_any = None
    bad_list = []

    for subdir in base_dir.iterdir():
        if not subdir.is_dir():
            continue

        files = sorted(subdir.glob("*"), key=lambda f: f.stat().st_mtime, reverse=True)
        files = [f for f in files if f.suffix.lower() in ALLOWED_EXTS][:MAX_FILES_PER_CATEGORY]

        for img in files:
            try:
                mtime = img.stat().st_mtime
            except FileNotFoundError:
                continue

            info = {
                "filename": img.name,
                "category": subdir.name,
                "timestamp": mtime,
                "url": f"/image/{camera}/{subdir.name}/{img.name}",
            }

            if (latest_any is None) or (mtime > latest_any["timestamp"]):
                latest_any = info

            if subdir.name.lower() != "good":
                bad_list.append(info)

    bad_list.sort(key=lambda d: d["timestamp"], reverse=True)
    return latest_any, bad_list[:10]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/image/<camera>/<category>/<filename>")
def serve_image(camera, category, filename):
    if camera not in CAMERA_DIRS:
        abort(404)
    directory = CAMERA_DIRS[camera] / category
    if not directory.exists():
        abort(404)
    return send_from_directory(directory, filename)

def monitor_changes():
    global last_known
    while True:
        for cam in CAMERA_DIRS:
            latest, bad = get_latest_any_and_bad(cam)
            if latest and (cam not in last_known or latest["timestamp"] > last_known[cam]):
                last_known[cam] = latest["timestamp"]
                socketio.emit("camera_update", {
                    "camera": cam,
                    "latest": latest,
                    "bad_recent": bad
                })
        time.sleep(0.3)

@socketio.on("connect")
def handle_connect():
    print("Client connected")

if __name__ == "__main__":
    thread = threading.Thread(target=monitor_changes, daemon=True)
    thread.start()
    socketio.run(app, host="0.0.0.0", port=8001, debug=True)
