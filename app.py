# app.py
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, send_from_directory, abort
from flask_socketio import SocketIO
from pathlib import Path

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Kamera → katalog bazowy
CAMERA_DIRS = {
    "X1": Path("/ftp/ftp/X1/new_images"),
    "Y1": Path("/ftp/ftp/Y1/new_images"),
}

ALLOWED_EXTS = {".jpg", ".jpeg", ".png"}
MAX_FILES_PER_CATEGORY = 100

def get_latest_any_and_bad(camera):
    base_dir = CAMERA_DIRS.get(camera)
    if not base_dir or not base_dir.exists():
        return None, []

    latest_any = None
    bad_list = []

    for subdir in base_dir.iterdir():
        if not subdir.is_dir():
            continue

        files = sorted(
            [f for f in subdir.glob("*") if f.suffix.lower() in ALLOWED_EXTS],
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:MAX_FILES_PER_CATEGORY]

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

def monitor_images():
    last_timestamps = {cam: 0 for cam in CAMERA_DIRS}
    while True:
        for cam in CAMERA_DIRS:
            latest, bad = get_latest_any_and_bad(cam)
            if latest and latest["timestamp"] > last_timestamps[cam]:
                last_timestamps[cam] = latest["timestamp"]
                socketio.emit("camera_update", {
                    "camera": cam,
                    "latest": latest,
                    "bad_recent": bad,
                })
        eventlet.sleep(0.3)

@socketio.on('connect')
def on_connect():
    print("WebSocket connected")

if __name__ == "__main__":
    eventlet.spawn(monitor_images)
    socketio.run(app, host="0.0.0.0", port=8000, debug=True)
