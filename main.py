import os
import time
import random
import aiofiles
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

STORE = {}
EXPIRY_HOURS = 24

def _cleanup_expired():
    now = time.time()
    expired = [
        k for k, v in STORE.items()
        if now - v["created_at"] > v.get("expiry_hours", EXPIRY_HOURS) * 3600
    ]
    for k in expired:
        path = STORE[k]["path"]
        if os.path.exists(path):
            os.remove(path)
        STORE.pop(k, None)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    expire_hours: int = Form(24)
):
    code = "".join(random.choices("0123456789", k=6))
    ts = time.time()
    filename = file.filename
    safe_filename = filename.replace(" ", "_")
    dest_path = os.path.join(UPLOAD_DIR, safe_filename)

    contents = await file.read()
    async with aiofiles.open(dest_path, 'wb') as out:
        await out.write(contents)

    size = len(contents)
    STORE[code] = {
        "filename": filename,
        "path": dest_path,
        "created_at": ts,
        "size": size,
        "expiry_hours": min(max(expire_hours, 1), 24 * 7)
    }

    download_url = request.url_for("download_page", code=code)
    return {"code": code, "download_url": str(download_url)}

@app.get("/d/{code}", response_class=HTMLResponse, name="download_page")
async def download_page(request: Request, code: str):
    _cleanup_expired()
    meta = STORE.get(code)
    if not meta:
        return templates.TemplateResponse("download.html", {"request": request, "error": "Invalid or expired code."})

    return templates.TemplateResponse("download.html", {
        "request": request,
        "code": code,
        "filename": meta["filename"],
        "size": meta["size"],
    })

@app.get("/d/{code}/file")
async def download_file(code: str):
    _cleanup_expired()
    meta = STORE.get(code)
    if not meta:
        raise HTTPException(status_code=404, detail="Invalid or expired code")

    path = meta["path"]
    if not os.path.exists(path):
        STORE.pop(code, None)
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path, filename=meta["filename"], media_type='application/octet-stream')
