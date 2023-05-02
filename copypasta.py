import base64
import os
from pathlib import Path
from OpenSSL import crypto, SSL

from flask import Flask, render_template, request, redirect, url_for, send_from_directory

from core import get_files

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = Path('uploads')

# Route for allowing loading of static assets
@app.route('/assets/<path:path>')
def assets(path):
    return send_from_directory('assets', path)


# Main Index
@app.route('/')
def index():
    
    host = request.host
    files = get_files(app.config['UPLOAD_FOLDER'])
    
    return render_template('index.html', files=files, host=host)


# Upload Path
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('uploaded_file', filename=filename))
    else:
        return "No file selected."


# Path to get and download
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    
    get_type = request.args.get('type')
    
    file = Path(app.config['UPLOAD_FOLDER']).joinpath(filename)
    
    if not file.exists():
        return b'File not found.'
    
    if get_type == 'raw':
        return send_from_directory(directory=app.config['UPLOAD_FOLDER'], path=filename)
    elif get_type == 'b64':
        return base64.b64encode(file.read_bytes())
    
    return b'Please provide the type parameter'


if __name__ == '__main__':
    app.run(debug=True)
    