# Automated Ephemeral File Sharing Portal

A high-performance, asynchronous web application designed to safely expose local NAS physical drives (like ZimaOS external HDDs) to the web and allow instantaneous, memory-efficient sharing of massive files (10GB+) via the GoFile.io API.

This project is built from the ground up using **FastAPI**, **Tailwind CSS**, and **asyncio** to ensure minimal resource utilization while maximizing I/O throughput.

---

## 1. Architecture and Workflow

The application acts as a lightweight, secure bridge between your physical server storage and the external internet.

1. **Local Storage Mounting**: Using Docker volumes, physical drives (e.g., `/mnt/external_hdd`) are mounted directly into the application container as read-only directories.
2. **Dynamic UI Rendering**: The FastAPI backend dynamically scans these directories and serves a modern, responsive HTML interface (powered by Tailwind CSS) allowing users to navigate folder structures in real-time.
3. **Memory-Efficient External Uploads**: When a user clicks "Share", the application does *not* download the file to the client, nor does it load the file into the server's RAM. Instead, it acts as a high-speed proxy. It opens a file stream from the local NAS and pipes it directly into an HTTP `POST` request to the GoFile.io API in small chunks.
4. **Link Generation**: Once the GoFile server acknowledges the upload, the API returns a public download link, which the frontend displays to the user.

---

## 2. Project Structure

```text
├── docker-compose.yml   # Orchestrates the container, maps physical drives to internal volumes, and exposes port 8000.
├── Dockerfile           # Builds the Python 3.11-slim image, installs dependencies, and sets the uvicorn entrypoint.
├── .env                 # Stores secure environment variables (GoFile API token, JSON mapping of shared directories).
├── requirements.txt     # Lists Python dependencies: fastapi, uvicorn, jinja2, python-dotenv, httpx, aiofiles.
└── app/                 # Core application directory
    ├── config.py        # Parses the .env file, mapping the SHARED_DIRS JSON into a Python dictionary.
    ├── main.py          # The FastAPI entrypoint containing the HTTP routes for browsing and sharing.
    ├── templates/       # Contains Jinja2 HTML templates.
    │   └── index.html   # The single-page responsive UI utilizing Tailwind CSS via CDN.
    └── services/        # Business logic modules.
        ├── files.py     # Contains `scan_directory` to read file metadata (size, mod-time).
        └── gofile.py    # Contains the complex chunked streaming logic interacting with the GoFile API.
```

---

## 3. Deep-Dive into the Source Code

### `app/main.py`: Routing and Security

The main file uses FastAPI to define the web endpoints. It is designed with robust path traversal protections to ensure users cannot escape the designated shared directories.

*   **The Root Endpoint (`/`)**:
    ```python
    @app.get("/", response_class=HTMLResponse)
    ```
    This endpoint iterates over the `SHARED_DIRS` dictionary loaded from `config.py`. It presents the highest level of your mounted drives as virtual "folders" on the UI.

*   **The Browse Endpoint (`/browse/{root_name}/{subpath:path}`)**:
    This is where path traversal protection occurs.
    ```python
    base_path = Path(SHARED_DIRS[root_name]).resolve(strict=True)
    target_path = Path(base_path / subpath.lstrip('/')).resolve()

    # Path traversal protection
    target_path.relative_to(base_path)
    ```
    By using Python's `pathlib.Path`, it resolves absolute file paths. The `relative_to` method acts as a strict security barrier: if the resolved `target_path` (e.g., if a user injected `../../../etc/passwd`) is not a strict child of the `base_path`, a `ValueError` is thrown and caught, returning a 403 Forbidden.

*   **The Share Endpoint (`/api/share/{root_name}/{subpath:path}`)**:
    Once the path is validated similarly to the browse endpoint, it triggers the upload logic:
    ```python
    download_link = await upload_file_to_gofile(str(target_path), GOFILE_API_TOKEN)
    ```

### `app/services/gofile.py`: Memory-Efficient Chunked Streaming

This is the most critical and complex part of the application. Uploading a 10GB+ file typically crashes lightweight servers if loaded entirely into RAM. To solve this, we construct a custom **asynchronous multipart/form-data generator**.

1.  **Server Allocation**: `get_gofile_server()` queries the API to find the optimal geographic server.
2.  **Boundary Construction**: The HTTP standard for file uploads requires unique boundaries separating the file payload from standard form data (like the API token). We generate a unique UUID and encode standard headers (`body_start`, `body_token`, `body_end`).
3.  **The Async Generator**:
    ```python
    async def file_sender():
        yield body_start
        async with aiofiles.open(file_path, "rb") as f:
            while chunk := await f.read(1024 * 1024):
                yield chunk
        yield body_token
        # ... yield body_folder, body_end
    ```
    This function yields the starting HTTP headers, and then uses `aiofiles` to read the massive file directly from the disk in safe **1MB chunks**. It yields these chunks one by one to the HTTP client.
4.  **Streaming Request**:
    ```python
    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(upload_url, content=file_sender(), headers=headers)
    ```
    `httpx.AsyncClient` consumes the `file_sender()` generator, maintaining a steady stream of data directly to GoFile.io without ever holding more than 1MB in server memory at any given time.

### Multi-File / Folder Uploads

The `upload_file_to_gofile` function detects if the requested path is a directory. If so, it:
1. Authenticates the account.
2. Creates a parent folder on the GoFile server.
3. Uses `os.walk` to iterate through the local directory recursively.
4. Uploads each individual file to the newly created remote folder using the same memory-efficient chunking logic.