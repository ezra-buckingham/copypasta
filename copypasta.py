from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, send_from_directory

from core import get_files, delete_files_in_dir

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
@app.route('/upload/file', methods=['POST'])
def upload_files():
    files = request.files.getlist('upload')
    filenames = []
    for file in files:
        if file:
            filename = file.filename
            file_location = Path(app.config['UPLOAD_FOLDER']).joinpath(filename)
            # If a file exists by that name
            if file_location.exists(): continue
            file.save(file_location)
            filenames.append(filename)
    if filenames:
        return redirect(url_for('index', action='upload', status='success'))
    else:
        return redirect(url_for('index', action='upload', status='failure'))
    
# Upload text
@app.route('/upload/text', methods=['POST'])
def upload_text():
    text = request.form.get('text')
    
    try:
        if text:
            filename = datetime.now().strftime('%d%b%Y_%H%M%S.txt')
            new_file = Path(app.config['UPLOAD_FOLDER']).joinpath(filename)
            new_file.write_text(text)
            return redirect(url_for('index', action='upload', status='success'))
    except:
        return redirect(url_for('index', action='upload', status='failure'))


# Delete file
@app.route('/delete/<file>', methods=['GET'])
def delete_file(file):
    
    file = Path(app.config['UPLOAD_FOLDER']).joinpath(file)
    
    try:
        if file.exists(): file.unlink()
        return redirect(url_for('index', action='delete', status='success'))
    except:
        return redirect(url_for('index', action='delete', status='failure'))


# Delete file
@app.route('/deleteall', methods=['GET'])
def delete_all_files():
    
    uploads = Path(app.config['UPLOAD_FOLDER'])
    
    try:
        delete_files_in_dir(uploads)
        return redirect(url_for('index', action='delete', status='success'))
    except:
        return redirect(url_for('index', action='delete', status='failure'))


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
    app.run(port=5000)