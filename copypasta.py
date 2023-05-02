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


# Upload files
@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('file')
    filenames = []
    for file in files:
        if file:
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            filenames.append(filename)
    if filenames:
        return redirect(url_for('index', action='upload', status='success'))
    else:
        return redirect(url_for('index', action='upload', status='failure'))
    

# Delete file
@app.route('/delete/<file>', methods=['GET'])
def delete_file(file):
    file = Path(app.config['UPLOAD_FOLDER']).joinpath(file)
    
    if file.exists(): file.unlink()
    return redirect(url_for('index', action='delete', status='success'))


# Get files
@app.route('/get/<file>', methods=['GET'])
def get_file(file):
    
    get_type = request.args.get('type')
    
    file = Path(app.config['UPLOAD_FOLDER']).joinpath(file)
    
    
    if get_type == 'raw':
        return send_from_directory(directory=app.config['UPLOAD_FOLDER'], path=file.name)
    elif get_type == 'b64':
        # Create / Get temp directory to generate the B64 file
        temp_directory = Path(app.config['UPLOAD_FOLDER']).joinpath('tmp')
        if not temp_directory.exists(): temp_directory.mkdir()
        
        b64_file = temp_directory.joinpath(f'{ file.name }.b64')
        b64_file.write_bytes(file.read_bytes())
        
        return send_from_directory(directory=temp_directory, path=b64_file.name)
    
    return b'Please provide the type parameter'


if __name__ == '__main__':
    app.run()
    