from fastapi import APIRouter, HTTPException
from models.search_models import SearchInput
from utils.query_builder import build_everything_query
from utils.search_engine import SearchEngine
from config.settings import settings
from utils.logger import get_logger
from utils.whoosh_indexer import WhooshIndexer
from utils.storage_helper import read_indexed_folders
from utils.response_helper import success_response, failure_response

router = APIRouter()
logger = get_logger()

# create whoosh instance and search engine
whoosh_indexer = WhooshIndexer(index_dir=settings.WHOOSH_INDEX_PATH)
search_engine = SearchEngine(whoosh_indexer=whoosh_indexer)

@router.post("/search")
def search(payload: SearchInput):
    if not payload.keyword:
        raise HTTPException(status_code=400, detail="keyword is required")

    # always use stored folders (do not accept folders in payload)
    folders = read_indexed_folders()
    if not folders:
        return failure_response(400, "No folders indexed. Use /api/add-folder first.", {"indexed_folders": []})

    if payload.search_mode == "filename":
        query = build_everything_query(payload, folders)
        try:
            data = search_engine.search_filename(query, payload)
            return success_response(200, "Filename search completed", data)
        # except Exception as e:
        #     logger.error(str(e))
        #     raise HTTPException(status_code=500, detail="Filename search failed")
        except HTTPException as http_err:
            raise http_err
        except Exception as e:
            logger.error(str(e))
            raise HTTPException(status_code=500, detail=str(e))

    elif payload.search_mode == "content":
        try:
            data = search_engine.search_content(payload)
            return success_response(200, "Content search completed", data)
        # except Exception as e:
        #     logger.error(str(e))
        #     raise HTTPException(status_code=500, detail="Content search failed")
        except HTTPException as http_err:
            raise http_err
        except Exception as e:
            logger.error(str(e))
            raise HTTPException(status_code=500, detail=str(e))


    else:
        raise HTTPException(status_code=400, detail="Invalid search_mode. Allowed: filename, content")
