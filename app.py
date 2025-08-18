# app.py
from flask import Flask, render_template, jsonify, send_file, abort
from pathlib import Path
from collections import deque

app = Flask(__name__)

CAMERA_DIRS = {
    "X1": Path("/ftp/ftp/X1/new_images"),
    "Y1": Path("/ftp/ftp/Y1/new_images"),
}

ALLOWED_EXTS = {".jpg", ".jpeg", ".png"}

bad_images_fifo = {camera: deque(maxlen=5) for camera in CAMERA_DIRS}
last_bad_timestamp = {camera: 0 for camera in CAMERA_DIRS}


def get_latest_images(camera, limit_bad=5):
    base_dir = CAMERA_DIRS[camera]
    if not base_dir.exists():
        return None, None, []

    latest_any = None
    latest_bad = None
    bad_list = []

    for category_dir in base_dir.iterdir():
        if not category_dir.is_dir():
            continue
        for img_path in category_dir.glob("*"):
            if img_path.suffix.lower() not in ALLOWED_EXTS:
                continue
            try:
                ts = img_path.stat().st_mtime
            except FileNotFoundError:
                continue

            info = {
                "filename": img_path.name,
                "category": category_dir.name,
                "timestamp": ts,
                "url": f"/image/{camera}/{category_dir.name}/{img_path.name}"
            }

            if latest_any is None or ts > latest_any["timestamp"]:
                latest_any = info

            if category_dir.name.lower() != "good":
                bad_list.append(info)
                if latest_bad is None or ts > latest_bad["timestamp"]:
                    latest_bad = info

    bad_list.sort(key=lambda x: x["timestamp"], reverse=True)
    return latest_any, latest_bad, bad_list[:limit_bad]


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

    global last_bad_timestamp, bad_images_fifo

    latest_any, latest_bad, recent_bad = get_latest_images(camera)

    if not bad_images_fifo[camera] and recent_bad:
        for item in reversed(recent_bad):
            bad_images_fifo[camera].append(item)
        last_bad_timestamp[camera] = recent_bad[0]["timestamp"]

    if latest_bad and latest_bad["timestamp"] > last_bad_timestamp[camera]:
        last_bad_timestamp[camera] = latest_bad["timestamp"]
        bad_images_fifo[camera].appendleft(latest_bad)

    return jsonify({
        "latest": latest_any,
        "bad_recent": list(bad_images_fifo[camera])
    })


@app.route("/image/<camera>/<category>/<filename>")
def serve_image(camera, category, filename):
    if camera not in CAMERA_DIRS:
        abort(404)
    img_path = CAMERA_DIRS[camera] / category / filename
    if not img_path.exists():
        abort(404)
    return send_file(img_path, mimetype="image/jpeg")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
