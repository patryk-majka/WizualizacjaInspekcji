from flask import Flask, render_template, send_from_directory, abort
import os

app = Flask(__name__)

# Konfiguracja katalogów kamer
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CAMERAS = {
    "X1": os.path.join(BASE_DIR, "X1"),
    "Y1": os.path.join(BASE_DIR, "Y1"),
}

@app.route("/")
def home():
    # Domyślnie przechodzimy do kamery X1
    return render_template("home.html", cameras=CAMERAS.keys())

@app.route("/kamera/<camera_id>")
def kamera_view(camera_id):
    if camera_id not in CAMERAS:
        abort(404, f"Kamera {camera_id} nie istnieje.")

    camera_path = CAMERAS[camera_id]
    good_dir = os.path.join(camera_path, "good")
    bad_dir = os.path.join(camera_path, "bad")

    # Pobierz listę zdjęć
    good_images = sorted(os.listdir(good_dir)) if os.path.exists(good_dir) else []
    bad_images = sorted(os.listdir(bad_dir)) if os.path.exists(bad_dir) else []

    # Identyfikacja zdjęć złych z kategoriami (nazwa katalogu)
    bad_images_info = []
    for fname in bad_images:
        bad_images_info.append({
            "filename": fname,
            "category": "bad"
        })

    # Link do przełączenia kamery
    other_camera = [c for c in CAMERAS if c != camera_id][0]

    return render_template(
        "kamera.html",
        camera_id=camera_id,
        other_camera=other_camera,
        good_images=good_images,
        bad_images_info=bad_images_info
    )

@app.route("/images/<camera_id>/<category>/<filename>")
def serve_image(camera_id, category, filename):
    if camera_id not in CAMERAS:
        abort(404)
    img_dir = os.path.join(CAMERAS[camera_id], category)
    return send_from_directory(img_dir, filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
