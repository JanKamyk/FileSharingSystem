import httpx
import aiofiles
import os
import uuid
from typing import Optional

async def get_gofile_server() -> str:
    """Fetch an available GoFile server."""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.gofile.io/servers")
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "ok":
            return data["data"]["servers"][0]["name"]
        raise Exception(f"Failed to get GoFile server: {data}")

async def upload_file_to_gofile(file_path: str, token: Optional[str] = None) -> str:
    """
    Upload a file to GoFile memory-efficiently using chunked streaming.
    Returns the downloadPage link on success.
    """
    server = await get_gofile_server()
    upload_url = f"https://{server}.gofile.io/contents/uploadfile"

    filename = os.path.basename(file_path)
    boundary = uuid.uuid4().hex.encode()

    # Multipart boundary markers
    body_start = b'--' + boundary + b'\r\n' + \
                 f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode() + \
                 b'Content-Type: application/octet-stream\r\n\r\n'

    body_token = b''
    if token:
        body_token = b'\r\n--' + boundary + b'\r\n' + \
                     b'Content-Disposition: form-data; name="token"\r\n\r\n' + \
                     token.encode()

    body_end = b'\r\n--' + boundary + b'--\r\n'

    async def file_sender():
        yield body_start
        async with aiofiles.open(file_path, "rb") as f:
            # Chunk size 1MB
            while chunk := await f.read(1024 * 1024):
                yield chunk
        yield body_token
        yield body_end

    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary.decode()}"
    }

    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(upload_url, content=file_sender(), headers=headers)
        response.raise_for_status()

        data = response.json()
        if data.get("status") == "ok":
            return data["data"]["downloadPage"]

        raise Exception(f"GoFile upload failed: {data}")
