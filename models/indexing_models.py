from pydantic import BaseModel
from typing import List

class FolderInput(BaseModel):
    folders: List[str]
