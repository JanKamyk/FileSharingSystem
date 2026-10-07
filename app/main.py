from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict

app = FastAPI(title="Automated Ephemeral File Sharing Portal")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}
