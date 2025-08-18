# app.py
from flask import Flask, render_template, jsonify, send_from_directory, abort
from pathlib import Path

app = Flask(__name__)

# Kamera → katalog bazowy
CAMERA_DIRS = {
    "X1": Path("/ftp/ftp/X1/new_images"),
    "Y1": Path("/ftp/ftp/Y1/new_images"),
}

ALLOWED_EXTS = {".jpg", ".jpeg", ".png"}
MAX_FILES_PER_CATEGORY = 100  # ograniczenie dla wydajności


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
    return latest_any, bad_list[:10] # Limit to 21 bad images for performance


@app.route("/")
def index():
    cameras_data = {}
    for cam in CAMERA_DIRS:
        latest, bad = get_latest_any_and_bad(cam)
        cameras_data[cam] = {
            "latest": latest,
            "bad_recent": bad
        }
    return render_template("index.html", cameras=cameras_data)


@app.route("/api/latest/<camera>")
def api_latest(camera):
    if camera not in CAMERA_DIRS:
        abort(404)

    latest_any, bad_recent = get_latest_any_and_bad(camera)
    return jsonify({
        "latest": latest_any,
        "bad_recent": bad_recent,
    })


@app.route("/image/<camera>/<category>/<filename>")
def serve_image(camera, category, filename):
    if camera not in CAMERA_DIRS:
        abort(404)
    directory = CAMERA_DIRS[camera] / category
    if not directory.exists():
        abort(404)
    return send_from_directory(directory, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
