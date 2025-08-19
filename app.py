from flask import Flask, render_template, send_from_directory, abort
from flask_socketio import SocketIO
from threading import Thread
from pathlib import Path
import time

app = Flask(__name__, static_folder="static", template_folder="templates")
socketio = SocketIO(app, cors_allowed_origins="*")

CAMERA_DIRS = {
    "X1": Path("/ftp/ftp/X1/new_images"),
    "Y1": Path("/ftp/ftp/Y1/new_images"),
}

ALLOWED_EXTS = {".jpg", ".jpeg", ".png"}
SEEN_FILES = {"X1": set(), "Y1": set()}

def watch_folder(camera):
    base_dir = CAMERA_DIRS[camera]
    if not base_dir.exists():
        print(f"[watcher] Directory for {camera} not found: {base_dir}")
        return

    while True:
        for subdir in base_dir.iterdir():
            if not subdir.is_dir():
                continue
            for file in sorted(subdir.glob("*")):
                if file.suffix.lower() not in ALLOWED_EXTS:
                    continue
                if file.name in SEEN_FILES[camera]:
                    continue
                try:
                    mtime = file.stat().st_mtime
                except FileNotFoundError:
                    continue
                info = {
                    "filename": file.name,
                    "category": subdir.name,
                    "timestamp": mtime,
                    "url": f"/image/{camera}/{subdir.name}/{file.name}",
                    "camera": camera,
                }
                SEEN_FILES[camera].add(file.name)
                socketio.emit("new_image", info)
        time.sleep(0.1)  # 100ms polling

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

def start_watchers():
    for cam in CAMERA_DIRS:
        thread = Thread(target=watch_folder, args=(cam,), daemon=True)
        thread.start()

start_watchers()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000)
