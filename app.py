from flask import Flask, render_template, jsonify, send_from_directory
from pathlib import Path

app = Flask(__name__)

BASE_DIR = Path("/ftp/ftp/X1/new_images")

def get_latest_image():
    images = []
    for subdir in BASE_DIR.iterdir():
        if subdir.is_dir():
            for img in subdir.glob("*.jpg"):
                images.append((img, subdir.name, img.stat().st_mtime))
    if not images:
        return None
    latest = max(images, key=lambda x: x[2])
    return {
        "filename": latest[0].name,
        "category": latest[1],
        "timestamp": latest[2],
        "path": f"{latest[1]}/{latest[0].name}"
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/latest")
def latest():
    latest = get_latest_image()
    return jsonify(latest)

@app.route("/static/img/<category>/<filename>")
def serve_image(category, filename):
    return send_from_directory(BASE_DIR / category, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
