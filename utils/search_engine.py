from fastapi import HTTPException
from .everything_api import call_everything
from .whoosh_indexer import WhooshIndexer
from models.search_models import SearchInput
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from utils.response_helper import success_response
from utils.storage_helper import read_indexed_folders
from .query_builder import build_everything_query
from config.settings import settings
from utils.abbreviation_ai import expand_abbreviations

class SearchEngine:
    def __init__(self, whoosh_indexer: WhooshIndexer):
        self.whoosh = whoosh_indexer

    def _parse_filters(self, payload: SearchInput):
        date_from = None
        date_to = None

        if payload.date_from:
            date_from = datetime.fromisoformat(payload.date_from)
            now = datetime.now()
            if date_from > now:
                raise ValueError("date_from cannot exceed today's date")

        if payload.date_to:
            dt = datetime.fromisoformat(payload.date_to)
            now = datetime.now()

            # If date_to is today → cap to current time
            if dt.date() == now.date():
                date_to = now
            else:
                date_to = dt.replace(hour=23, minute=59, second=59)

            if date_to > now:
                raise ValueError("date_to cannot exceed today's date")


        # range-order check
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from cannot be greater than date_to")

        size_from_b = int(float(payload.size_from) * 1024) if payload.size_from is not None else None
        size_to_b = int(float(payload.size_to) * 1024) if payload.size_to is not None else None

        file_types = None
        if payload.file_types and payload.file_types != ["all"]:
            file_types = [ft.lower().lstrip('.') for ft in payload.file_types]

        return date_from, date_to, size_from_b, size_to_b, file_types


    def search_filename(self, query: str, payload: SearchInput):
        #print(f"[DEBUG] raw user keyword = {query}")

        # --- AI abbreviation expansion ---
        if settings.ENABLE_ABBREVIATION_AI:
            expanded = expand_abbreviations(query)
            if expanded and expanded != query:
                #print(f"[DEBUG] AI expanded keyword = {expanded}")
                payload.keyword = expanded    # << CRITICAL FIX

        folders = read_indexed_folders()

        # build Everything.exe query USING THE UPDATED KEYWORD
        everything_query = build_everything_query(payload, folders)
        #(f"[DEBUG] everything_query = {everything_query}")

        # delegate to Everything API
        raw = call_everything(everything_query)
        #print("everything raw",raw)
        items = raw.get("results") or raw.get("items") or raw.get("files") or []
        #date_from, date_to, size_from_b, size_to_b, file_types = self._parse_filters(payload)

        try:
            date_from, date_to, size_from_b, size_to_b, file_types = self._parse_filters(payload)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Enforce "current date not exceed logger" — cap date_to to now
        now = datetime.now()
        if date_to and date_to > now:
            date_to = now

        results = []
        for it in items:
            # build full path
            full_path = it.get("fullpath") or None
            if not full_path:
                folder = it.get("path")
                file_name = it.get("name")
                full_path = f"{folder}/{file_name}" if folder and file_name else None

            # size (Everything usually returns bytes)
            size_b = None
            try:
                raw_size = it.get("size")
                if raw_size is not None:
                    size_b = int(raw_size)
            except Exception:
                size_b = None

            # size filters
            if size_from_b and (size_b is None or size_b < size_from_b):
                continue
            if size_to_b and (size_b is None or size_b > size_to_b):
                continue

            # parse modified date robustly into a datetime object (local time)
            modified_raw = it.get('date_modified') or it.get('modified') or None
            mod_dt = None
            mod_str = None
            if modified_raw:
                try:
                    s = str(modified_raw).strip()
                    # FILETIME numeric (Everything often returns Windows FILETIME)
                    if s.isdigit():
                        ft = int(s)
                        # FILETIME -> seconds since epoch conversion
                        # (ft - 116444736000000000) / 10_000_000 gives seconds since Unix epoch
                        mod_dt = datetime.fromtimestamp((ft - 116444736000000000) / 10_000_000)
                    else:
                        # Try a few common formats. Prefer ISO first.
                        try:
                            mod_dt = datetime.fromisoformat(s)
                        except Exception:
                            try:
                                mod_dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
                            except Exception:
                                try:
                                    mod_dt = datetime.strptime(s, "%Y-%m-%d")
                                except Exception:
                                    # fallback: try parsing as timestamp in seconds (float)
                                    try:
                                        ts = float(s)
                                        mod_dt = datetime.fromtimestamp(ts)
                                    except Exception:
                                        mod_dt = None
                    if mod_dt:
                        mod_str = mod_dt.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        mod_str = s  # keep raw if we couldn't parse to dt
                except Exception:
                    mod_dt = None
                    mod_str = str(modified_raw)

            # Apply date filters (if date_from/to provided, skip if cannot parse timestamp)
            # Note: date_from/date_to are datetimes (date_to already made inclusive to end-of-day in _parse_filters)
            if date_from:
                if not mod_dt or mod_dt < date_from:
                    continue
            if date_to:
                if not mod_dt or mod_dt > date_to:
                    continue

            # file type
            ftype = None
            if it.get('name'):
                ftype = Path(it.get('name')).suffix.lower().lstrip('.')
            if file_types and ftype not in file_types:
                continue

            results.append({
                "file_name": it.get("name"),
                "path": full_path,
                "size_kb": int(size_b/1024) if size_b else None,
                "modified": mod_str
            })
            if payload.max_results and len(results) >= payload.max_results:
                break

        return {"results_count": len(results), "results": results}


    def search_content(self, payload: SearchInput):
        terms = [t.strip() for t in payload.keyword.split(',') if t.strip()]

        raw_kw = payload.keyword
        #print(f"[DEBUG] raw user keyword = {raw_kw}")

        # --- AI abbreviation expansion ---
        if settings.ENABLE_ABBREVIATION_AI:
            expanded = expand_abbreviations(raw_kw)
            if expanded and expanded != raw_kw:
                #print(f"[DEBUG] AI expanded keyword = {expanded}")
                payload.keyword = expanded

        # REBUILD TERMS **after expansion**
        terms = [t.strip() for t in payload.keyword.split(',') if t.strip()]
        #print(f"[DEBUG] whoosh_query_terms = {terms}")

        if not terms:
            return {"results_count": 0, "results": []}
        q = " OR ".join([f'"{t}"' for t in terms])
        #date_from, date_to, size_from_b, size_to_b, file_types = self._parse_filters(payload)
        try:
            date_from, date_to, size_from_b, size_to_b, file_types = self._parse_filters(payload)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        hits = self.whoosh.search(q, limit=payload.max_results, date_from=date_from, date_to=date_to, size_from_b=size_from_b, size_to_b=size_to_b, case_sensitive=payload.case_sensitive, whole_word=payload.whole_word, file_types=file_types)
        return {"results_count": len(hits), "results": hits}
