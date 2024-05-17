import os
import random
import re
from flask import Flask, request, render_template, redirect, url_for, session
import pandas as pd

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'supersecretkey'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'locations' not in request.files or 'services' not in request.files:
        return 'No files uploaded!', 400

    locations_file = request.files['locations']
    services_file = request.files['services']

    if locations_file.filename == '' or services_file.filename == '':
        return 'No selected file', 400

    # Ensure the upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    locations_path = os.path.join(app.config['UPLOAD_FOLDER'], locations_file.filename)
    services_path = os.path.join(app.config['UPLOAD_FOLDER'], services_file.filename)

    locations_file.save(locations_path)
    services_file.save(services_path)

    generated_content, toc = generate_content(locations_path, services_path)
    session['generated_content'] = generated_content
    session['toc'] = toc

    return redirect(url_for('show_content'))

def generate_content(locations_path, services_path):
    locations_df = pd.read_csv(locations_path)
    services_df = pd.read_csv(services_path)

    generated_content = []
    toc = []

    for _, loc_row in locations_df.iterrows():
        for _, serv_row in services_df.iterrows():
            post_title = spintax(f"{serv_row['name']} in {loc_row['name']}")
            post_content = spintax(f"{serv_row['desc']} available in {loc_row['name']}.")
            post_image = serv_row['img']

            generated_content.append({
                'title': post_title,
                'content': post_content,
                'image': post_image
            })

            toc.append(post_title)

    return generated_content, toc

def spintax(text):
    pattern = re.compile(r'\{([^{}]*)\}')
    while True:
        match = pattern.search(text)
        if not match:
            break
        options = match.group(1).split('|')
        text = text[:match.start()] + random.choice(options) + text[match.end():]
    return text

@app.route('/content')
def show_content():
    generated_content = session.get('generated_content', [])
    toc = session.get('toc', [])
    return render_template('content.html', generated_content=generated_content, toc=toc)

if __name__ == '__main__':
    app.run(debug=True)
