from flask import Flask, render_template, jsonify
import os
import time

app = Flask(__name__)

# Katalog ze zdjęciami
IMAGE_DIR = os.path.join('static', 'img', 'new_images')

# Bufor ostatnich 5 zdjęć innych niż "good"
last_bad_images = []

def get_all_images():
    """Zwraca listę wszystkich zdjęć z katalogu, posortowaną po czasie modyfikacji malejąco."""
    files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(IMAGE_DIR, x)), reverse=True)
    return files

def update_bad_images():
    """Aktualizuje listę ostatnich 5 zdjęć, które nie są 'good'."""
    global last_bad_images
    all_images = get_all_images()

    # Filtrujemy zdjęcia, które nie zawierają 'good' w nazwie
    bad_images = [img for img in all_images if 'good' not in img.lower()]

    # Jeśli jest nowe zdjęcie inne niż 'good', aktualizujemy listę
    if bad_images and (not last_bad_images or bad_images[0] != last_bad_images[0]):
        for img in bad_images:
            if img not in last_bad_images:
                last_bad_images.insert(0, img)  # dodaj na początek
        last_bad_images = last_bad_images[:5]  # FIFO – max 5 elementów

@app.route('/')
def index():
    all_images = get_all_images()
    update_bad_images()
    return render_template('index.html', all_images=all_images, last_bad_images=last_bad_images)

@app.route('/get_bad_images')
def get_bad_images():
    """Zwraca JSON z ostatnimi 5 zdjęciami innymi niż 'good'."""
    update_bad_images()
    return jsonify(last_bad_images)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
