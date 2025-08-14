from flask import Flask, render_template, jsonify
from pathlib import Path
from collections import deque

app = Flask(__name__)

# Katalog źródłowy (fizyczny) ze zdjęciami:
BASE_DIR = Path("/ftp/ftp/X1/new_images")

# Dozwolone rozszerzenia (możesz dopisać kolejne)
ALLOWED_EXTS = {".jpg", ".jpeg", ".png"}

def get_latest_image():
    """
    Skanuje tylko katalogi bezpośrednio pod BASE_DIR (1 poziom),
    wybiera najnowszy plik o dozwolonym rozszerzeniu.
    Zwraca dict z filename, category, timestamp i gotowym URL do <img>.
    """
    if not BASE_DIR.exists():
        return None

    latest = None

    # Iteruj po kategoriach (good, zgrzew, itp.)
    for subdir in BASE_DIR.iterdir():
        if not subdir.is_dir():
            continue

        # Iteruj po plikach w danej kategorii
        try:
            for img in subdir.iterdir():
                if not img.is_file():
                    continue
                if img.suffix.lower() not in ALLOWED_EXTS:
                    continue
                try:
                    mtime = img.stat().st_mtime
                except FileNotFoundError:
                    # Plik mógł zostać usunięty w trakcie – pomijamy
                    continue

                if (latest is None) or (mtime > latest["timestamp"]):
                    latest = {
                        "filename": img.name,
                        "category": subdir.name,
                        "timestamp": mtime,
                        # UWAGA: korzystamy z domyślnego /static + Twojego symlinka
                        # static/img/new_images -> /ftp/ftp/X1/new_images
                        "url": f"/static/img/new_images/{subdir.name}/{img.name}",
                    }
        except PermissionError:
            # Gdyby któryś folder był niedostępny – pomijamy
            continue

    return latest

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/latest")
def api_latest():
    return jsonify(get_latest_image())

if __name__ == "__main__":
    # port 8000 jak wcześniej, debug dla wygody
    app.run(host="0.0.0.0", port=8000, debug=True)
