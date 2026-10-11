import os
from datetime import datetime
from typing import List, Dict, Union

def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = 0
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_name[i]}".rstrip("0").rstrip(".") if i > 0 else f"{int(size_bytes)} {size_name[i]}"

async def scan_directory(path: str) -> List[Dict[str, Union[str, int]]]:
    """
    Scans a directory and returns a list of file details.

    Returns:
        List of dicts containing:
        - filename: str
        - size: str (human readable)
        - modified: str (YYYY-MM-DD HH:MM:SS)
    """
    files = []

    try:
        if not os.path.exists(path):
            return files

        if not os.path.isdir(path):
            return files

        # Using scandir for better performance
        for entry in os.scandir(path):
            try:
                stat = entry.stat()
                mod_time = datetime.fromtimestamp(stat.st_mtime)
                if entry.is_file():
                    files.append({
                        "filename": entry.name,
                        "type": "file",
                        "size": format_size(stat.st_size),
                        "modified": mod_time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                elif entry.is_dir():
                    files.append({
                        "filename": entry.name,
                        "type": "folder",
                        "size": "-",
                        "modified": mod_time.strftime("%Y-%m-%d %H:%M:%S")
                    })
            except OSError:
                # Skip files we can't access
                continue

    except OSError as e:
        print(f"Error scanning directory {path}: {e}")
        # Return empty list on permission or other OS errors
        pass

    return files
