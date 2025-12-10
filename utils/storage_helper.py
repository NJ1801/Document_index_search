import json
from pathlib import Path
from typing import List, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
STORAGE_DIR = ROOT / "storage"
INDEX_FILE = STORAGE_DIR / "indexed_folders.json"
INDEX_META_FILE = STORAGE_DIR / "index_meta.json" 

def ensure_storage():
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_FILE.exists():
        INDEX_FILE.write_text("[]", encoding="utf-8")

def read_indexed_folders() -> List[str]:
    ensure_storage()
    try:
        data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []

def append_folders(folders: List[str]) -> List[str]:
    ensure_storage()
    current = read_indexed_folders()
    for f in folders:
        f = str(Path(f))
        if f not in current:
            current.append(f)
    INDEX_FILE.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return current

# -----------------------------
# Index metadata helpers (new)
# -----------------------------
def read_index_meta() -> Dict[str, str]:
    """
    Returns a mapping { absolute_path: isoformat_mtime_string }
    """
    ensure_storage()
    try:
        data = json.loads(INDEX_META_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        return {}

def write_index_meta(meta: Dict[str, str]) -> None:
    ensure_storage()
    try:
        INDEX_META_FILE.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    except Exception:
        # best-effort — don't crash caller
        pass