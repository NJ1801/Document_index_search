from fastapi import APIRouter, HTTPException
from models.content_models import FileContentRequest
from utils.whoosh_extractors import EXTRACTORS
from pathlib import Path
from utils.logger import get_logger
from utils.response_helper import success_response

router = APIRouter()
logger = get_logger()

@router.post("/show-content")
def show_content(payload: FileContentRequest):
    p = Path(payload.file_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="File not found")
    extractor = EXTRACTORS.get(p.suffix.lower())
    if not extractor:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    text = extractor(p)
    if text is None:
        raise HTTPException(status_code=404, detail="Could not extract content")

    size_kb = int(p.stat().st_size / 1024) if p.exists() else None
    modified = datetime_from_mtime(p.stat().st_mtime)
    return success_response(200, "File content extracted", {"path": str(p.resolve()), "filename": p.name, "filetype": p.suffix.lower().lstrip('.'), "size_kb": size_kb, "modified": modified, "content_text": text})

# helper local to route file
def datetime_from_mtime(mtime):
    from datetime import datetime
    return datetime.utcfromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
