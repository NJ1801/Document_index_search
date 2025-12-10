from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
from utils.logger import get_logger
from utils.response_helper import failure_response

logger = get_logger()

def register_exception_handlers(app: FastAPI, logger=logger):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(f"HTTP error: {exc.detail}")
        return JSONResponse(failure_response(exc.status_code, exc.detail), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error: {exc}")
        return JSONResponse(failure_response(400, "Invalid input data"), status_code=400)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        tb = traceback.format_exc()
        logger.error(tb)
        return JSONResponse(failure_response(500, "Internal server error"), status_code=500)
