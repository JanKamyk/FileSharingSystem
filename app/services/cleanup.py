import os
import time

async def cleanup_old_files(directory: str, max_age_hours: int = 24) -> None:
    """
    Scans the given directory and permanently deletes files older than
    the specified max_age_hours based on modification time.
    """
    try:
        if not os.path.exists(directory) or not os.path.isdir(directory):
            return

        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        for entry in os.scandir(directory):
            if entry.is_file():
                try:
                    stat = entry.stat()
                    file_age_seconds = current_time - stat.st_mtime

                    if file_age_seconds > max_age_seconds:
                        os.remove(entry.path)
                        print(f"Deleted old file: {entry.path}")
                except OSError as e:
                    print(f"Error accessing or deleting file {entry.path}: {e}")

    except OSError as e:
        print(f"Error scanning directory for cleanup {directory}: {e}")
