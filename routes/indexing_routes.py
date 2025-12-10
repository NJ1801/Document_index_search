from fastapi import APIRouter, HTTPException
from models.indexing_models import FolderInput
from utils.storage_helper import append_folders, read_indexed_folders
from config.settings import settings
from utils.logger import get_logger
from utils.whoosh_indexer import WhooshIndexer
from utils.response_helper import success_response, failure_response

router = APIRouter()
logger = get_logger()

# create a module-level indexer (safe to reuse)
whoosh_indexer = WhooshIndexer(index_dir=settings.WHOOSH_INDEX_PATH)

@router.get("/list-folders")
def list_folders():
    folders = read_indexed_folders()
    return success_response(200, "Indexed folders retrieved", {"indexed_folders": folders})


@router.post("/add-folder")
def add_folder(payload: FolderInput):
    if not payload.folders:
        raise HTTPException(status_code=400, detail="folders is required")

    updated = append_folders(payload.folders)

    indexed = {}
    total = 0

    for f in payload.folders:
        try:
            count = whoosh_indexer.index_folder(f)
            indexed[f] = count
            total += count
            logger.info(f"Indexed {count} files in {f}")
        except Exception as e:
            logger.error(f"Error indexing {f}: {e}")
            indexed[f] = 0

    return success_response(200, "Folders added and indexed successfully", {
        "indexed_counts": indexed,
        "total_indexed": total,
        "watcher_enabled": settings.ENABLE_WATCHER
    })
