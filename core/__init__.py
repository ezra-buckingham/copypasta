from pathlib import Path
from hashlib import md5
from datetime import datetime


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"


def delete_files_in_dir(path: Path):
    
    for file in path.glob('*'):
        # If a directory, move on
        if Path(file).is_dir(): continue
        
        file.unlink()


def get_files(path: Path):

    files = []
    
    for file in path.glob('*'):
        # If a directory, move on
        if Path(file).is_dir(): continue
        
        # Pretty print the size
        size = file.lstat().st_size
        size = sizeof_fmt(size)
        
        # Generate the MD5
        md5sum = md5(file.read_bytes()).hexdigest()
        
        # Generate the time
        ctime = datetime.fromtimestamp(file.stat().st_ctime).strftime('%d %b %Y %H:%M:%S')
        
        # Append and then sort on the date
        files.append([file.name, size, ctime, md5sum])
        files.sort(key=lambda item: datetime.strptime(item[2], '%d %b %Y %H:%M:%S'), reverse=True)
        
    return files
