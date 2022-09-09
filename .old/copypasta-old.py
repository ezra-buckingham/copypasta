import base64
from datetime import datetime
from hashlib import md5
from math import ceil
import os

from jinja2 import Environment, BaseLoader
import web

# Tool is not designed for security, but might as disable this unless needed
web.config.debug = False


urls = ('/b64/.*$', 'B64',                  # For accessing base64-encoded versions of files
        '/clipboard', 'Clipboard',          # For getting the text on the "clipboard"
        '/list$', 'List',                   # To list files available for download
        '/remove/.*$', 'Remove',            # Remove a given file
        '/[0-9]{1,}$', 'DownloadShortcut',  # For downloading files by index number shortcut
        '.*$', 'Index')                     # Main page

MAIN_TEMPLATE = """
<html>
  <head>
    <title>CopyPasta</title>
  </head>
  <body>
    <style>
    body{ font-family: 'Arial'}
    a:link { color: black; }
    a:visited { color: gray; }
    </style>

    <script>
    confirmRemove(file) {
    var ans;
    if (confirm("Remove " + file "?") == true) {
       ans == "
      } 
    }
    </script>

    <h2 id="header">Paste</h2>
    <form action="./index" method="post">
      <textarea id="text" name="text" rows="5" cols="30">{{ text }}</textarea>
      <br><br>
      <button name="paste" type="submit" title="Paste text to this input area">Paste</button>
      <button name="save_text" type="submit" title="Save pasted text as a file available for download">Save text</button>
      <button name="save_b64" type="submit" title="Save a base64-encoded blob as a file available for download">Save B64 file</button>
    </form>
    <pre>curl -F text="your text here" {{ host }}</pre>
    <pre>curl -F text="$(cat file.txt)" {{ host }}</pre>

    <br>
    <h2 id="header">Upload</h2>
    <form action="./index" method="post" enctype="multipart/form-data">
      <input type="file" id="file" name="upload">
      <button type="submit">Upload</button>
    </form>
    <pre>curl -F upload=@/path/to/file {{ host }}</pre>

    <br>
    <h2 id="header">Download</h2>
    {% if downloads %}
    <table style="border-collapse: collapse; border-spacing: 100px 0;">
    <tr>
      <th>Index</th>
      <th>File</th>
      <th>Download</th>
      <th>Preview</th>
      <th>To Base64</th>
      <th>Remove</th>
      <th>Size</th>
      <th>Date</th>
      <th>MD5</th>
    </tr>
    {% for file in downloads %}
    <tr style="background-color: {{ loop.cycle('white', 'lightgray') }}">
      <td style="padding: 10px;">{{ loop.index }}</td>
      <td style="padding: 10px;">{{ file[0] }}</td>
      <td style="padding: 10px;"><a href="{{ file[1] }}" download>{{ download_icon }}</a></td>
      <td style="padding: 10px;"><a href="{{ file[1] }}">{{ preview_icon }}</a></td>
      <td style="padding: 10px;"><a href="./b64/{{ file[0] }}">{{ to_b64_icon }}</a></td>
      <td style="padding: 10px;"><a href="./remove/{{ file[0] }}" onclick="return confirm('Remove {{ file[0] }}?')";>{{ remove_icon }}</a></td>
      <td style="padding: 10px;">{{ file[2] }}</td>
      <td style="padding: 10px;">{{ file[3] }}</td>
      <td style="padding: 10px;">{{ file[4] }}</td>
    </tr>
    {% endfor %}
    </table>
    {% endif %}
    <pre>curl {{ host }}/&lt;index&gt; -L -o &lt;filename&gt;</pre>

    <br>
    <h2 id="header">Copy</h2>
    <pre>curl {{ host }}/clipboard | xclip -selection clipboard</pre>

    <br>
    <h2 id="header">Use from remote host with SSH</h2>
    <pre>ssh user@remote-host -R 8000:{{ host }}</pre>

    <br>
    <h2 id="header">~/.bashrc functions</h2>
    <pre>
export COPYPASTA="{{ host }}"


copy () {
    curl $COPYPASTA/clipboard -s | xclip -selection clipboard
}


paste () {
    local input=""

    if [[ -p /dev/stdin ]]; then
        input="$(cat -)"
    else
        input="${@}"
    fi

    curl -F text="$input" $COPYPASTA
}


upload () {
    curl -F upload=@"$1" $COPYPASTA -s
    echo "[*] Uploaded $1 to $COPYPASTA."
}


download () {
    curl $COPYPASTA/$1 -L -o $2
}


downloads () {
    if [ "$1" = "-a" ] || [ "$1" = "--all" ]; then
        DETAILS="true"
    else
        DETAILS="false"
    fi
    curl $COPYPASTA/list?details=$DETAILS
}
</pre>


  </body>
</html>
"""


DOWNLOADS_TEMPLATE = """
{% for file in files %}
[{{ '%2s'|format(loop.index) -}}
] {{ file[0] -}}
{% if details -%}
{{ ' ' * (max_length + 1 - file[0]|length) -}}
{{ host -}}
{{ file[1][1:] -}}
{{ ' ' * (max_length + 1 - file[0]|length) -}}
{{ '%4s'|format(file[2]) -}}
{{ ' ' }}{{ file[3]|replace(' ', '', 2) -}}
{{ ' ' }}{{ file[4] -}}
{% endif -%}
{% endfor %}


"""


def get_static_files():
    """Build a list of lists, with each item in the list representing a file in the ./static directory.
    Include the attributes filename, path, size, creation time, and MD5. Return list sorted by date.
    The ./static/ directory is a builtin feature of web.py.
    """

    static_files = []
    for file in os.listdir('./static'):  # web.py automatically treats files in static directory as such
        path = './static/' + file
        size = os.stat(path).st_size
        if size > 1048576:
            size = str(ceil(size / 1048576)) + 'M'
        elif 1048576 > size > 1024:
            size = str(ceil(size / 1024)) + 'K'
        else:
            size = str(size) + 'B'
        md5sum = md5(open(path, 'rb').read()).hexdigest()
        # Better way to do this? converting to string, then converting back to datetime object for sorting.
        ctime = datetime.fromtimestamp(os.stat(path).st_ctime).strftime('%d %b %Y %H:%M:%S')
        static_files.append([file, path, size, ctime, md5sum])
        static_files.sort(key=lambda item: datetime.strptime(item[3], '%d %b %Y %H:%M:%S'), reverse=True)
    return static_files


class B64:
    """ Generate base64-encoded versions of files stored in the ./static/ directory.
    Return to the user as a text blob in the browser.
    """

    def GET(self):
        file = web.ctx.env['PATH_INFO'].split('/')[-1]
        if file in os.listdir('./static'):
            with open('./static/' + file, 'rb') as f:
                data = f.read()
                b64_data = base64.b64encode(data)
            web.header('Content-Type', 'text/plain')
            return b64_data
        raise web.seeother('/')


class Clipboard:

    def GET(self):
        with open('clipboard', 'r') as f:
            text = f.read()
        return text


class List:

    def GET(self):
        details = web.input().get('details')
        if details and details.lower() in ['true', 'yes']:
            details = True
        else:
            details = False
        files = get_static_files()
        max_length = 0
        host = web.ctx.env['HTTP_HOST']
        for file in files:
            max_length = len(file[0]) if len(file[0]) > max_length else max_length
        template = Environment(loader=BaseLoader).from_string(DOWNLOADS_TEMPLATE)
        return template.render(max_length=max_length,
                               host=host,
                               files=files,
                               details=details)


class DownloadShortcut:
    """Provide a convenient shortcut to download files in the ./static/ directory
    by index number.
    """

    def GET(self):
        # Convert the path to an int and drop the leading '/'
        files = get_static_files()
        file_index = int(web.ctx.env['PATH_INFO'][1:])
        if int(file_index) > len(files):
            raise web.seeother('/')
        else:
            raise web.seeother('./static/' + files[file_index - 1][0])

class Remove:
    """Remove a given file from the server."""
    def GET(self):
        file = web.ctx.env['PATH_INFO'].split('/')[-1]
        if file in os.listdir('./static'):
            os.remove('./static/' + file)
        raise web.seeother('/')


class Index:
    """Handle all GET and POST requests other than those directed at /b64.
    Displays current text held in "clipboard" and list of available downloads.
    """

    def GET(self):
        if not web.ctx.env['PATH_INFO'] == '/':
            raise web.seeother('/')
        host = web.ctx.env['HTTP_HOST']
        download_icon = """
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-download" viewBox="0 0 16 16" title="Download">
                  <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                  <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
                  <title>Download</title>
                </svg>
                """
        preview_icon = """
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-eyeglasses" viewBox="0 0 16 16">
                  <path d="M4 6a2 2 0 1 1 0 4 2 2 0 0 1 0-4zm2.625.547a3 3 0 0 0-5.584.953H.5a.5.5 0 0 0 0 1h.541A3 3 0 0 0 7 8a1 1 0 0 1 2 0 3 3 0 0 0 5.959.5h.541a.5.5 0 0 0 0-1h-.541a3 3 0 0 0-5.584-.953A1.993 1.993 0 0 0 8 6c-.532 0-1.016.208-1.375.547zM14 8a2 2 0 1 1-4 0 2 2 0 0 1 4 0z"/>
                  <title>Preview</title>
                </svg>
                """
        to_b64_icon = """
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-file-code" viewBox="0 0 16 16">
                  <path d="M6.646 5.646a.5.5 0 1 1 .708.708L5.707 8l1.647 1.646a.5.5 0 0 1-.708.708l-2-2a.5.5 0 0 1 0-.708l2-2zm2.708 0a.5.5 0 1 0-.708.708L10.293 8 8.646 9.646a.5.5 0 0 0 .708.708l2-2a.5.5 0 0 0 0-.708l-2-2z"/>
                  <path d="M2 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2zm10-1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1z"/>
                  <title>Convert to Base64</title>
                </svg>
                """
        remove_icon = """
               <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
                 <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                 <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
              </svg>
              """

        # Use a file in case app crashes, last pasted input remains
        with open('clipboard', 'r') as f:
            text = f.read()
        downloads = get_static_files()
        template = Environment(loader=BaseLoader).from_string(MAIN_TEMPLATE)
        return template.render(text=text,
                               host=host,
                               downloads=downloads,
                               download_icon=download_icon,
                               preview_icon=preview_icon,
                               to_b64_icon=to_b64_icon,
                               remove_icon=remove_icon)

    def POST(self):
        # If user wants to simply paste text to the "clipboard"
        # Use a file in case app crashes, last pasted input remains
        if all([k in ['paste', 'text'] for k in web.input().keys()]):
            text = web.input().get('text')  # Don't care if it's empty
            with open('clipboard', 'w') as f:
                f.write(text)
                raise web.seeother('/')

        # If user wants to save pasted text to a text file
        if all([k in ['save_text', 'text'] for k in web.input().keys()]):
            text = web.input().get('text')
            if text:
                filename = datetime.now().strftime('%d%b%Y_%H%M%S.txt')
                with open('./static/' + filename, 'w') as f:
                    f.write(text)
                raise web.seeother('/')
            else:
                raise web.seeother('/')

        # If user wants to save a Base64-encoded blob as a (decoded) file
        if all([k in ['save_b64', 'text'] for k in web.input().keys()]):
            text = web.input().get('text').encode()
            if text:
                filename = datetime.now().strftime('%d%b%Y_%H%M%S')
                data = base64.b64decode(text)
                with open('./static/' + filename, 'wb') as f:
                    f.write(data)
                raise web.seeother('/')
            else:
                raise web.seeother('/')

        file = web.input().get('upload')
        if file:
            ul = web.input(upload={})
            storage_dir = './static'
            if 'upload' in ul:
                filepath = ul.upload.filename.replace('\\', '/')
                filename = filepath.split('/')[-1]
                file_out = open(storage_dir + '/' + filename, 'wb')
                file_out.write(ul.upload.file.read())
            raise web.seeother('/')

        return


if __name__ == '__main__':
    if not os.path.exists('./clipboard'):
        with open('./clipboard', 'wb') as f:
            f.write(b'')
    if not os.path.exists('./static/'):
        os.mkdir('./static')
    app = web.application(urls, globals())
    app.run()
