# app.py
from flask import Flask, render_template, jsonify, send_from_directory, abort
from pathlib import Path
from collections import deque

app = Flask(__name__)

# Katalogi bazowe dla kamer
CAMERA_DIRS = {
    "X1": Path("/ftp/ftp/X1/new_images"),
    "Y1": Path("/ftp/ftp/Y1/new_images"),
}

ALLOWED_EXTS = {".jpg", ".jpeg", ".png"}

# FIFO na ostatnie 5 złych zdjęć (osobno dla każdej kamery)
bad_images_fifo = {
    "X1": deque(maxlen=5),
    "Y1": deque(maxlen=5),
}
last_bad_timestamp = {
    "X1": 0,
    "Y1": 0,
}


def get_latest_any_and_bad(camera, limit_bad=5):
    """
    Zwraca:
      - latest_any: dict z najnowszym zdjęciem (dowolna kategoria)
      - latest_bad: dict z najnowszym złym zdjęciem (katalog inny niż 'good')
      - top_bad:   lista dictów z ostatnimi 'limit_bad' złymi zdjęciami
    """
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
                    if (latest_bad is None) or (mtime > latest_bad["timestamp"]):
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

    global last_bad_timestamp, bad_images_fifo

    latest_any, latest_bad, top_bad = get_latest_any_and_bad(camera, limit_bad=5)

    if not bad_images_fifo[camera] and top_bad:
        for item in reversed(top_bad):
            bad_images_fifo[camera].append(item)
        last_bad_timestamp[camera] = top_bad[0]["timestamp"]

    if latest_bad and latest_bad["timestamp"] > last_bad_timestamp[camera]:
        last_bad_timestamp[camera] = latest_bad["timestamp"]
        bad_images_fifo[camera].appendleft(latest_bad)

    return jsonify({
        "latest": latest_any,
        "bad_recent": list(bad_images_fifo[camera])
    })


@app.route("/image/<camera>/<category>/<filename>")
def serve_image(camera, category, filename):
    """
    Serwuje obrazki bez potrzeby symlinków.
    """
    if camera not in CAMERA_DIRS:
        abort(404)
    directory = CAMERA_DIRS[camera] / category
    if not directory.exists():
        abort(404)
    return send_from_directory(directory, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
