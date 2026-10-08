from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, AsyncGenerator
from contextlib import asynccontextmanager
import os
import asyncio

from app.config import SHARED_DIRS, GOFILE_API_TOKEN
from app.services.files import scan_directory
from app.services.gofile import upload_file_to_gofile
from pathlib import Path

app = FastAPI(title="Automated Ephemeral File Sharing Portal")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request) -> HTMLResponse:
    # List root directories
    roots = []
    for root_name, path in SHARED_DIRS.items():
        if os.path.isdir(path):
            roots.append({
                "filename": root_name,
                "type": "folder",
                "size": "-",
                "modified": "-"
            })
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"files": roots, "current_path": "/", "is_root": True, "breadcrumbs": []}
    )

@app.get("/browse/{root_name}", response_class=HTMLResponse)
@app.get("/browse/{root_name}/{subpath:path}", response_class=HTMLResponse)
async def browse(request: Request, root_name: str, subpath: str = "") -> HTMLResponse:
    if root_name not in SHARED_DIRS:
        return HTMLResponse(content="Root directory not found", status_code=404)

    try:
        base_path = Path(SHARED_DIRS[root_name]).resolve(strict=True)
        # Using / to join paths prevents absolute paths from overriding the base
        # But we still strip leading slashes from subpath just in case
        target_path = Path(base_path / subpath.lstrip('/')).resolve()
    except FileNotFoundError:
        return HTMLResponse(content="Directory not found", status_code=404)

    # Path traversal protection
    try:
        target_path.relative_to(base_path)
    except ValueError:
        return HTMLResponse(content="Invalid path", status_code=403)

    if not target_path.is_dir():
        return HTMLResponse(content="Directory not found", status_code=404)

    files = await scan_directory(str(target_path))

    # Generate breadcrumbs
    parts = [p for p in subpath.split("/") if p]
    breadcrumbs = []
    current_bpath = ""
    for part in parts:
        current_bpath = f"{current_bpath}/{part}" if current_bpath else part
        breadcrumbs.append({"name": part, "path": f"/browse/{root_name}/{current_bpath}"})

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "files": files,
            "current_path": f"/browse/{root_name}/{subpath}" if subpath else f"/browse/{root_name}",
            "is_root": False,
            "root_name": root_name,
            "subpath": subpath,
            "breadcrumbs": breadcrumbs
        }
    )

@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/api/share/{root_name}/{subpath:path}")
async def share_file(root_name: str, subpath: str) -> JSONResponse:
    if root_name not in SHARED_DIRS:
        return JSONResponse(status_code=404, content={"error": "Root directory not found"})

    try:
        base_path = Path(SHARED_DIRS[root_name]).resolve(strict=True)
        target_path = Path(base_path / subpath.lstrip('/')).resolve()
    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"error": "File or folder not found"})

    # Path traversal protection
    try:
        target_path.relative_to(base_path)
    except ValueError:
        return JSONResponse(status_code=403, content={"error": "Invalid path"})

    if target_path == base_path:
        # Prevent sharing the root directory itself
        return JSONResponse(status_code=403, content={"error": "Cannot share root directory"})

    # Security/existence check
    if not target_path.exists():
        return JSONResponse(status_code=404, content={"error": "File or folder not found"})

    try:
        download_link = await upload_file_to_gofile(str(target_path), GOFILE_API_TOKEN)
        return JSONResponse(content={"link": download_link})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
