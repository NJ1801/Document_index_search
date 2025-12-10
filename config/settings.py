import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DOTENV = ROOT / ".env"
if DOTENV.exists():
    load_dotenv(DOTENV)

class Settings:
    EVERYTHING_URL: str = os.environ.get("EVERYTHING_URL", "http://localhost:8989/")
    WHOOSH_INDEX_PATH: str = os.environ.get("WHOOSH_INDEX_PATH", str(ROOT / "storage" / "whoosh_index"))
    ALLOWED_EXTS = [".pdf", ".docx", ".txt", ".csv", ".xlsx", ".xls", ".pptx", ".ppt"]
    ENABLE_WATCHER: bool = os.environ.get("ENABLE_WATCHER", "false").lower() == "true"
    LOG_FILE = str(ROOT / "logs" / "app.log")

settings = Settings()
