import base64
from datetime import datetime
from hashlib import md5
from math import ceil
import os
from pathlib import Path
from OpenSSL import crypto, SSL

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


def cert_gen(
    emailAddress="emailAddress",
    commonName="commonName",
    countryName="NT",
    localityName="localityName",
    stateOrProvinceName="stateOrProvinceName",
    organizationName="organizationName",
    organizationUnitName="organizationUnitName",
    serialNumber=0,
    validityStartInSeconds=0,
    validityEndInSeconds=10*365*24*60*60,
    KEY_FILE = "c2_key.pem",
    CERT_FILE="c2_cert.pem"):
    
    # Create the Private Key
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 4096)
    
    # Create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = countryName
    cert.get_subject().ST = stateOrProvinceName
    cert.get_subject().L = localityName
    cert.get_subject().O = organizationName
    cert.get_subject().OU = organizationUnitName
    cert.get_subject().CN = commonName
    cert.get_subject().emailAddress = emailAddress
    cert.set_serial_number(serialNumber)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(validityEndInSeconds)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha512')
    
    with open(CERT_FILE, "wt") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))
    with open(KEY_FILE, "wt") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode("utf-8"))

        
def get_main_template():
    main_template = Path('templates/index.html').read_text()
    return main_template


def get_downloads_template():
    downloads_template = Path('templates/downloads.html').read_text()
    return downloads_template

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
        template = Environment(loader=BaseLoader).from_string(get_downloads_template())
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

        # Use a file in case app crashes, last pasted input remains
        with open('clipboard', 'r') as f:
            text = f.read()
        downloads = get_static_files()
        template = Environment(loader=BaseLoader).from_string(get_main_template())
        return template.render(text=text, host=host, downloads=downloads)

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
