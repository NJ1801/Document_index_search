from datetime import datetime

def format_mtime(mtime):
    try:
        return datetime.utcfromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None
