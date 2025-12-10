from pydantic import BaseModel

class FileContentRequest(BaseModel):
    file_path: str
