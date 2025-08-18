# app.py
from flask import Flask, render_template, jsonify, send_from_directory, abort
from pathlib import Path
from collections import deque
import threading

app = Flask(__name__)

CAMERA_DIRS = {
    "X1": Path("/ftp/ftp/X1/new_images"),
    "Y1": Path("/ftp/ftp/Y1/new_images"),
}

ALLOWED_EXTS = {".jpg", ".jpeg", ".png"}

# Chronione przez lock – osobno dla każdej kamery
bad_images_fifo = {
    "X1": deque(maxlen=5),
    "Y1": deque(maxlen=5),
}
last_bad_timestamp = {
    "X1": 0,
    "Y1": 0,
}
fifo_lock = threading.Lock()

def get_latest_any_and_bad(camera, limit_bad=5):
    base_dir = CAMERA_DIRS.get(camera)
    if not base_dir or not base_dir.exists():
        return None, None, []

    latest_any = None
    latest_bad = None
    bad_list = []

    for subdir in base_dir.iterdir():
        if not subdir.is_dir():
            continue
        try:
            for img in subdir.iterdir():
                if not img.is_file():
                    continue
                if img.suffix.lower() not in ALLOWED_EXTS:
                    continue
                try:
                    mtime = img.stat().st_mtime
                except (FileNotFoundError, PermissionError):
                    continue

                info = {
                    "filename": img.name,
                    "category": subdir.name,
                    "timestamp": mtime,
                    "url": f"/image/{camera}/{subdir.name}/{img.name}",
                }

                if latest_any is None or mtime > latest_any["timestamp"]:
                    latest_any = info

                if subdir.name.lower() != "good":
                    bad_list.append(info)
                    if latest_bad is None or mtime > latest_bad["timestamp"]:
                        latest_bad = info
        except PermissionError:
            continue

    bad_list.sort(key=lambda d: d["timestamp"], reverse=True)
    top_bad = bad_list[:limit_bad]
    return latest_any, latest_bad, top_bad


@app.route("/")
@app.route("/<camera>")
def index(camera="X1"):
    if camera not in CAMERA_DIRS:
        abort(404)
    return render_template("index.html", camera=camera)


@app.route("/api/latest/<camera>")
def api_latest(camera):
    if camera not in CAMERA_DIRS:
        abort(404)

    latest_any, latest_bad, top_bad = get_latest_any_and_bad(camera)

    with fifo_lock:
        if not bad_images_fifo[camera] and top_bad:
            for item in reversed(top_bad):
                bad_images_fifo[camera].append(item)
            last_bad_timestamp[camera] = top_bad[0]["timestamp"]

        if latest_bad and latest_bad["timestamp"] > last_bad_timestamp[camera]:
            last_bad_timestamp[camera] = latest_bad["timestamp"]
            bad_images_fifo[camera].appendleft(latest_bad)

        return jsonify({
            "latest": latest_any if latest_any else {},
            "bad_recent": list(bad_images_fifo[camera])
        })


@app.route("/image/<camera>/<category>/<filename>")
def serve_image(camera, category, filename):
    if camera not in CAMERA_DIRS:
        abort(404)
    directory = CAMERA_DIRS[camera] / category
    file_path = directory / filename

    if not file_path.exists() or not file_path.is_file():
        abort(404)

    try:
        return send_from_directory(directory, filename)
    except Exception:
        abort(500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False, threaded=True)
