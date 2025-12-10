from fastapi import FastAPI
from config.settings import settings
from routes.indexing_routes import router as indexing_router
from routes.search_routes import router as search_router
from routes.content_routes import router as content_router
from utils.logger import get_logger
from utils.exceptions import register_exception_handlers

app = FastAPI(title="Everything + Whoosh Search API")
logger = get_logger()
register_exception_handlers(app, logger)

app.include_router(indexing_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(content_router, prefix="/api")

from utils.response_helper import success_response

@app.get("/")
def root():
    return success_response(200, "API running", {"endpoints": ["/api/add-folder","/api/list-folders","/api/search","/api/show-content"]})
