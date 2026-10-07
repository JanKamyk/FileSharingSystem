import os
from dotenv import load_dotenv

load_dotenv()

SHARED_DIR: str = os.getenv("SHARED_DIR", "./test_files")
GOFILE_API_TOKEN: str | None = os.getenv("GOFILE_API_TOKEN")
