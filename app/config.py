import os
from dotenv import load_dotenv

load_dotenv()

import json

_shared_dirs_env = os.getenv("SHARED_DIRS", '{"Movies": "./app/movies", "Music": "./app/music"}')
try:
    SHARED_DIRS: dict[str, str] = json.loads(_shared_dirs_env)
except json.JSONDecodeError:
    SHARED_DIRS = {"Movies": "./app/movies", "Music": "./app/music"}
GOFILE_API_TOKEN: str | None = os.getenv("GOFILE_API_TOKEN")
