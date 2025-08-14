from flask import Flask, render_template
import os

app = Flask(__name__)

# Ścieżka bazowa do zdjęć w symlinkowanym katalogu
BASE_IMAGE_DIR = '/ftp/ftp/X1/new_images'

@app.route('/')
def index():
    grouped_images = {}

    for root, dirs, files in os.walk(BASE_IMAGE_DIR):
        # Pomijamy ukryte pliki
        files = [f for f in files if not f.startswith('.')]
        if not files:
            continue

        # Kategoria = podkatalog względem BASE_IMAGE_DIR (np. 'zgrzew', 'good', 'bad1')
        category = os.path.relpath(root, BASE_IMAGE_DIR)

        # Ścieżki względem katalogu 'img' (bo symlink: static/img → /ftp/ftp/X1)
        images = [os.path.join('new_images', category, f) for f in sorted(files)]

        grouped_images[category] = images

    return render_template('index.html', grouped_images=grouped_images)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
