from flask import Flask, render_template, jsonify
from pathlib import Path
from collections import deque

app = Flask(__name__)

BASE_DIR = Path("/ftp/ftp/Y1/new_images")
ALLOWED_EXTS = {".jpg", ".jpeg", ".png"}

# FIFO na ostatnie 5 złych zdjęć (nie "good")
bad_images_fifo = deque(maxlen=5)
last_bad_timestamp = 0  # timestamp najnowszego złego zdjęcia już znanego (dla wykrywania nowości)


def get_latest_any_and_bad(limit_bad=5):
    """
    Zwraca:
      - latest_any: dict z najnowszym zdjęciem (dowolna kategoria)
      - latest_bad: dict z najnowszym złym zdjęciem (katalog inny niż 'good')
      - top_bad:   lista dictów z ostatnimi 'limit_bad' złymi zdjęciami (posortowane malejąco po czasie)
    """
    latest_any = None
    latest_bad = None
    bad_list = []

    if not BASE_DIR.exists():
        return None, None, []

    for subdir in BASE_DIR.iterdir():
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
                    "url": f"/static/imgy/new_images/{subdir.name}/{img.name}",
                }

                if (latest_any is None) or (mtime > latest_any["timestamp"]):
                    latest_any = info

                if subdir.name.lower() != "good":
                    bad_list.append(info)
                    if (latest_bad is None) or (mtime > latest_bad["timestamp"]):
                        latest_bad = info
        except PermissionError:
            continue

    # posortuj złe malejąco po czasie i weź limit
    bad_list.sort(key=lambda d: d["timestamp"], reverse=True)
    top_bad = bad_list[:limit_bad]
    return latest_any, latest_bad, top_bad


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/latest")
def api_latest():
    global last_bad_timestamp, bad_images_fifo

    latest_any, latest_bad, top_bad = get_latest_any_and_bad(limit_bad=5)

    # Inicjalizacja FIFO przy pierwszym razie – pokaż od razu 5 ostatnich złych
    if not bad_images_fifo and top_bad:
        for item in top_bad:
            bad_images_fifo.append(item)  # kolejność będzie od najstarszego do najnowszego w deque
        # ustaw najnowszy timestamp
        last_bad_timestamp = top_bad[0]["timestamp"]

    # Jeśli pojawiło się nowsze złe zdjęcie – dodaj na początek (FIFO)
    if latest_bad and latest_bad["timestamp"] > last_bad_timestamp:
        last_bad_timestamp = latest_bad["timestamp"]
        bad_images_fifo.appendleft(latest_bad)

    # Zwróć odpowiedź
    return jsonify({
        "latest": latest_any,
        "bad_recent": list(bad_images_fifo)
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
