from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict

from app.config import SHARED_DIR
from app.services.files import scan_directory

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
