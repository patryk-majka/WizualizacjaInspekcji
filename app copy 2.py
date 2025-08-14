from flask import Flask, render_template, jsonify
from pathlib import Path
from collections import deque

app = Flask(__name__)

BASE_DIR = Path("/ftp/ftp/X1/new_images")
ALLOWED_EXTS = {".jpg", ".jpeg", ".png"}

# FIFO na ostatnie 5 złych zdjęć
bad_images_fifo = deque(maxlen=5)
last_bad_timestamp = 0


def scan_latest():
    """Zwraca tuple: (najnowsze zdjęcie dowolne, najnowsze zdjęcie złe)"""
    if not BASE_DIR.exists():
        return None, None

    latest_any = None
    latest_bad = None

    for subdir in BASE_DIR.iterdir():
        if not subdir.is_dir():
            continue
        try:
            for img in subdir.iterdir():
                if not img.is_file() or img.suffix.lower() not in ALLOWED_EXTS:
                    continue
                try:
                    mtime = img.stat().st_mtime
                except FileNotFoundError:
                    continue

                img_info = {
                    "filename": img.name,
                    "category": subdir.name,
                    "timestamp": mtime,
                    "url": f"/static/img/new_images/{subdir.name}/{img.name}"
                }

                # najnowsze dowolne
                if (latest_any is None) or (mtime > latest_any["timestamp"]):
                    latest_any = img_info

                # najnowsze złe (nie good)
                if subdir.name.lower() != "good":
                    if (latest_bad is None) or (mtime > latest_bad["timestamp"]):
                        latest_bad = img_info

        except PermissionError:
            continue

    return latest_any, latest_bad


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/latest")
def api_latest():
    global last_bad_timestamp

    latest_any, latest_bad = scan_latest()
    if latest_bad and latest_bad["timestamp"] > last_bad_timestamp:
        last_bad_timestamp = latest_bad["timestamp"]
        bad_images_fifo.appendleft(latest_bad)

    return jsonify({
        "latest": latest_any,
        "bad_recent": list(bad_images_fifo)
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
