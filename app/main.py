from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Dict
import os

from app.config import SHARED_DIR, GOFILE_API_TOKEN
from app.services.files import scan_directory
from app.services.gofile import upload_file_to_gofile

app = FastAPI(title="Automated Ephemeral File Sharing Portal")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request) -> HTMLResponse:
    files = await scan_directory(SHARED_DIR)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"files": files, "shared_dir": SHARED_DIR}
    )

@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/api/share/{filename}")
async def share_file(filename: str) -> JSONResponse:
    file_path = os.path.join(SHARED_DIR, filename)

    # Security/existence check
    if not os.path.isfile(file_path):
        return JSONResponse(status_code=404, content={"error": "File not found"})

    try:
        download_link = await upload_file_to_gofile(file_path, GOFILE_API_TOKEN)
        return JSONResponse(content={"link": download_link})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
