import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import Optional
from pydantic import BaseModel
from app.dependencies import require_role

router = APIRouter()

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


class UploadResponse(BaseModel):
    success: bool
    url: str
    filename: str


@router.post("/upload/image")
async def upload_image(file: UploadFile = File(...), _=Depends(require_role("admin", "sales"))):
    print(f"Upload request - filename: {file.filename}, size: {file.size}")
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过5MB")
    
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="只允许上传图片文件(jpg, png, gif, webp)")
    
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过5MB")
    
    import uuid
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / filename
    
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    
    return {
        "success": True,
        "data": {
            "url": f"/uploads/{filename}",
            "filename": filename
        }
    }


@router.get("/uploads/{filename}")
async def get_uploaded_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path)