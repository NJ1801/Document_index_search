import time
import requests
from config.settings import settings
from requests.utils import requote_uri

def call_everything(query: str, timeout: int = 60):
    base = settings.EVERYTHING_URL.rstrip("/") + "/"
    params = (
        f"json=1"
        f"&path_column=1"
        f"&fullpath=1"
        f"&size_column=1"
        f"&date_modified_column=1"
        f"&s={requote_uri(query)}"
    )
    url = base + "?" + params

    last_exc = None
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_exc = e
            time.sleep(1)
    raise last_exc
