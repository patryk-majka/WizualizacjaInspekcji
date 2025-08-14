from flask import Flask, render_template, send_from_directory, abort
import os

app = Flask(__name__)

# Ścieżka bazowa do katalogów kamer
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/kamera/<camera_id>')
def kamera(camera_id):
    # Sprawdzamy czy kamera jest X1 lub Y1
    if camera_id not in ['X1', 'Y1']:
        abort(404)

    camera_path = os.path.join(BASE_DIR, camera_id)

    # Lista klas (podkatalogów)
    try:
        classes = sorted([d for d in os.listdir(camera_path) if os.path.isdir(os.path.join(camera_path, d))])
    except FileNotFoundError:
        abort(404)

    # Zbieramy zdjęcia z podkatalogów
    images = {}
    for cls in classes:
        cls_path = os.path.join(camera_path, cls)
        imgs = sorted([f for f in os.listdir(cls_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
        images[cls] = imgs

    # Link do drugiej kamery
    other_camera = 'Y1' if camera_id == 'X1' else 'X1'

    return render_template('index.html', camera_id=camera_id, other_camera=other_camera, images=images)

@app.route('/img/<camera_id>/<cls>/<filename>')
def serve_image(camera_id, cls, filename):
    # Bezpieczeństwo: nie pozwalamy na wyjście poza katalog
    if camera_id not in ['X1', 'Y1']:
        abort(404)
    directory = os.path.join(BASE_DIR, camera_id, cls)
    return send_from_directory(directory, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
