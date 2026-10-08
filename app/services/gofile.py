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

async def get_account_id(token: str) -> str:
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("https://api.gofile.io/accounts/getid", headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "ok":
            return data["data"]["id"]
        raise Exception(f"Failed to get account ID: {data}")

async def get_root_folder_id(token: str, account_id: str) -> str:
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"https://api.gofile.io/accounts/{account_id}", headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "ok":
            return data["data"]["rootFolder"]
        raise Exception(f"Failed to get root folder ID: {data}")

async def set_content_public(token: str, content_id: str) -> None:
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "attribute": "public",
            "attributeValue": True
        }
        response = await client.put(f"https://api.gofile.io/contents/{content_id}/update", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "ok":
            print(f"Warning: Failed to set content public: {data}")

async def create_folder(token: str, parent_folder_id: str, folder_name: str) -> tuple[str, str]:
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "parentFolderId": parent_folder_id,
            "folderName": folder_name,
            "public": True
        }
        response = await client.post("https://api.gofile.io/contents/createFolder", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "ok":
            # Returns folderId, and we construct the download link with its code
            return data["data"]["id"], f"https://gofile.io/d/{data['data']['code']}"
        raise Exception(f"Failed to create folder: {data}")

async def _upload_single_file(file_path: str, token: Optional[str] = None, folder_id: Optional[str] = None) -> str:
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

    body_folder = b''
    if folder_id:
        body_folder = b'\r\n--' + boundary + b'\r\n' + \
                      b'Content-Disposition: form-data; name="folderId"\r\n\r\n' + \
                      folder_id.encode()

    body_end = b'\r\n--' + boundary + b'--\r\n'

    async def file_sender():
        yield body_start
        async with aiofiles.open(file_path, "rb") as f:
            # Chunk size 1MB
            while chunk := await f.read(1024 * 1024):
                yield chunk
        yield body_token
        yield body_folder
        yield body_end

    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary.decode()}"
    }

    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(upload_url, content=file_sender(), headers=headers)
        response.raise_for_status()

        data = response.json()
        if data.get("status") == "ok":
            file_id = data["data"].get("fileId")
            if token and file_id:
                await set_content_public(token, file_id)
            return data["data"]["downloadPage"]

        raise Exception(f"GoFile upload failed: {data}")

async def upload_file_to_gofile(file_path: str, token: Optional[str] = None) -> str:
    """
    Upload a file or directory to GoFile memory-efficiently using chunked streaming.
    Returns the downloadPage link on success.
    """
    if os.path.isfile(file_path):
        return await _upload_single_file(file_path, token)

    if os.path.isdir(file_path):
        if not token:
            raise Exception("GoFile API token is required to upload folders.")

        account_id = await get_account_id(token)
        root_folder_id = await get_root_folder_id(token, account_id)

        folder_name = os.path.basename(file_path.rstrip(os.sep))
        new_folder_id, folder_download_link = await create_folder(token, root_folder_id, folder_name)

        # Iteratively upload all files in the directory to the new folder
        for root, _, files in os.walk(file_path):
            for file in files:
                current_file_path = os.path.join(root, file)
                await _upload_single_file(current_file_path, token, new_folder_id)

        return folder_download_link

    raise Exception("Path is neither a file nor a directory.")
