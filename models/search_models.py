from pydantic import BaseModel, Field
from typing import List, Optional

class SearchInput(BaseModel):
    keyword: str = Field(..., example="invoice")
    search_mode: str = Field(..., example="filename")  # filename or content
    file_types: Optional[List[str]] = Field(default_factory=lambda: ["all"])
    date_from: Optional[str] = None  # YYYY-MM-DD or None
    date_to: Optional[str] = None
    size_from: Optional[float] = None  # in KB
    size_to: Optional[float] = None    # in KB
    case_sensitive: bool = False
    whole_word: bool = False
    max_results: int = 100
