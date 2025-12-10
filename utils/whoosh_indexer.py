# # # from whoosh import index as whoosh_index
# # # from whoosh.fields import Schema, TEXT, ID, NUMERIC
# # # from whoosh.analysis import StemmingAnalyzer
# # # from whoosh.qparser import MultifieldParser
# # # # Use Corrector (works across common whoosh builds)
# # # from whoosh.spelling import Corrector
# # # from pathlib import Path
# # # from datetime import datetime
# # # from typing import Optional, List
# # # from .whoosh_extractors import EXTRACTORS
# # # import os

# # # class WhooshIndexer:
# # #     def __init__(self, index_dir: str):
# # #         self.index_dir = Path(index_dir)
# # #         self.schema = self._get_schema()
# # #         self.ix = self._open_or_create()
# # #         self.spell = None
# # #         self._ensure_spellchecker()

# # #     def _get_schema(self):
# # #         return Schema(
# # #             path=ID(stored=True, unique=True),
# # #             filename=TEXT(stored=True, analyzer=StemmingAnalyzer()),
# # #             filetype=ID(stored=True),
# # #             modified=ID(stored=True),
# # #             size_bytes=NUMERIC(stored=True),
# # #             content=TEXT(stored=True, analyzer=StemmingAnalyzer()),
# # #         )

# # #     def _open_or_create(self):
# # #         if not self.index_dir.exists():
# # #             self.index_dir.mkdir(parents=True, exist_ok=True)
# # #         if whoosh_index.exists_in(str(self.index_dir)):
# # #             return whoosh_index.open_dir(str(self.index_dir))
# # #         return whoosh_index.create_in(str(self.index_dir), self.schema)

# # #     def _ensure_spellchecker(self):
# # #         try:
# # #             self.spell = Corrector(self.ix.reader(), fieldname='content')
# # #         except Exception:
# # #             self.spell = None

# # #     def add_or_update(self, path: Path, content: str):
# # #         writer = self.ix.writer()
# # #         try:
# # #             modified = datetime.utcfromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
# # #             size_b = path.stat().st_size
# # #             writer.update_document(
# # #                 path=str(path.resolve()),
# # #                 filename=path.name,
# # #                 filetype=path.suffix.lower().lstrip('.'),
# # #                 modified=modified,
# # #                 size_bytes=size_b,
# # #                 content=content,
# # #             )
# # #             writer.commit()
# # #             self._ensure_spellchecker()
# # #         except Exception:
# # #             try:
# # #                 writer.cancel()
# # #             except Exception:
# # #                 pass

# # #     def index_folder(self, folder: str, allowed_exts: Optional[List[str]] = None):
# # #         allowed = set(allowed_exts) if allowed_exts else set(EXTRACTORS.keys())
# # #         p = Path(folder)
# # #         if not p.exists() or not p.is_dir():
# # #             return 0
# # #         count = 0
# # #         for file in p.rglob("*"):
# # #             if not file.is_file():
# # #                 continue
# # #             suffix = file.suffix.lower()
# # #             if suffix not in allowed:
# # #                 continue
# # #             extractor = EXTRACTORS.get(suffix)
# # #             if not extractor:
# # #                 continue
# # #             try:
# # #                 content = extractor(file)
# # #             except Exception:
# # #                 content = None
# # #             if content:
# # #                 self.add_or_update(file, content)
# # #                 count += 1
# # #         return count

# # #     def _format_snippet(self, hit, field="content"):
# # #         raw = hit.highlights(field, top=1) or ""
# # #         if not raw:
# # #             txt = hit.get(field, "")[:200]
# # #             return (txt.replace("\n", " ").strip() + "...") if txt else ""
# # #         single = raw.replace("\n", " ")
# # #         single = ' '.join(single.split())
# # #         return single

# # #     def _post_filter(self, docs, date_from=None, date_to=None, size_from_b=None, size_to_b=None, case_sensitive=False, whole_word=False, file_types=None):
# # #         from datetime import datetime
# # #         results = []
# # #         for h in docs:
# # #             try:
# # #                 modified = h.get('modified')
# # #                 size_b = h.get('size_kb') and int(h.get('size_kb') * 1024) or None
# # #                 ftype = h.get('filetype')
# # #             except Exception:
# # #                 continue
# # #             if date_from or date_to:
# # #                 try:
# # #                     mod_dt = datetime.strptime(modified, "%Y-%m-%d %H:%M:%S")
# # #                 except Exception:
# # #                     continue
# # #                 if date_from and mod_dt < date_from:
# # #                     continue
# # #                 if date_to and mod_dt > date_to:
# # #                     continue
# # #             if size_from_b and (size_b is None or size_b < size_from_b):
# # #                 continue
# # #             if size_to_b and (size_b is None or size_b > size_to_b):
# # #                 continue
# # #             if file_types and file_types != ['all']:
# # #                 if ftype and ftype.lower() not in [ft.lower() for ft in file_types]:
# # #                     continue
# # #             results.append(h)
# # #         return results

# # #     def search(self, query: str, limit: int = 50, date_from=None, date_to=None, size_from_b=None, size_to_b=None, case_sensitive=False, whole_word=False, file_types=None):
# # #         with self.ix.searcher() as searcher:
# # #             parser = MultifieldParser(["content", "filename"], schema=self.ix.schema)
# # #             q = parser.parse(query)
# # #             hits = searcher.search(q, limit=limit)
# # #             docs = []
# # #             for h in hits:
# # #                 docs.append({
# # #                     'path': h.get('path'),
# # #                     'filename': h.get('filename'),
# # #                     'filetype': h.get('filetype'),
# # #                     'modified': h.get('modified'),
# # #                     'size_kb': int(h.get('size_bytes') / 1024) if h.get('size_bytes') is not None else None,
# # #                     'score': float(h.score),
# # #                     'snippet': self._format_snippet(h, 'content')
# # #                 })

# # #             # spelling corrections when no docs
# # #             if not docs and self.spell:
# # #                 suggestions = []
# # #                 for term in query.split():
# # #                     try:
# # #                         s = self.spell.suggest(term)
# # #                         if s:
# # #                             suggestions.extend(s[:1])
# # #                     except Exception:
# # #                         pass
# # #                 if suggestions:
# # #                     sug_q = " | ".join([f'"{s}"' for s in suggestions])
# # #                     try:
# # #                         sq = parser.parse(sug_q)
# # #                         sh = searcher.search(sq, limit=limit)
# # #                         for h in sh:
# # #                             docs.append({
# # #                                 'path': h.get('path'),
# # #                                 'filename': h.get('filename'),
# # #                                 'filetype': h.get('filetype'),
# # #                                 'modified': h.get('modified'),
# # #                                 'size_kb': int(h.get('size_bytes') / 1024) if h.get('size_bytes') is not None else None,
# # #                                 'score': float(h.score),
# # #                                 'snippet': self._format_snippet(h, 'content')
# # #                             })
# # #                     except Exception:
# # #                         pass

# # #             filtered = self._post_filter(docs, date_from=date_from, date_to=date_to, size_from_b=size_from_b, size_to_b=size_to_b, case_sensitive=case_sensitive, whole_word=whole_word, file_types=file_types)
# # #             return filtered




# # import re
# # from whoosh import index as whoosh_index
# # from whoosh.fields import Schema, TEXT, ID, NUMERIC
# # from whoosh.analysis import StemmingAnalyzer
# # from whoosh.qparser import MultifieldParser
# # from whoosh.spelling import Corrector
# # from pathlib import Path
# # from datetime import datetime
# # from typing import Optional, List
# # from .whoosh_extractors import EXTRACTORS
# # import os


# # class WhooshIndexer:
# #     def __init__(self, index_dir: str):
# #         self.index_dir = Path(index_dir)
# #         self.schema = self._get_schema()
# #         self.ix = self._open_or_create()
# #         self.spell = None
# #         self._ensure_spellchecker()

# #     # ----------------------------------------------------------
# #     # SCHEMA
# #     # ----------------------------------------------------------
# #     def _get_schema(self):
# #         return Schema(
# #             path=ID(stored=True, unique=True),
# #             filename=TEXT(stored=True, analyzer=StemmingAnalyzer()),
# #             filetype=ID(stored=True),
# #             modified=ID(stored=True),
# #             size_bytes=NUMERIC(stored=True),
# #             content=TEXT(stored=True, analyzer=StemmingAnalyzer()),
# #         )

# #     # ----------------------------------------------------------
# #     # INDEX SETUP
# #     # ----------------------------------------------------------
# #     def _open_or_create(self):
# #         if not self.index_dir.exists():
# #             self.index_dir.mkdir(parents=True, exist_ok=True)

# #         if whoosh_index.exists_in(str(self.index_dir)):
# #             return whoosh_index.open_dir(str(self.index_dir))

# #         return whoosh_index.create_in(str(self.index_dir), self.schema)

# #     def _ensure_spellchecker(self):
# #         try:
# #             self.spell = Corrector(self.ix.reader(), fieldname='content')
# #         except Exception:
# #             self.spell = None

# #     # ----------------------------------------------------------
# #     # INCREMENTAL INDEXING HELPERS
# #     # ----------------------------------------------------------
# #     def _indexed_mtime(self, path: Path) -> Optional[str]:
# #         """Return stored mtime or None if file not indexed."""
# #         with self.ix.searcher() as s:
# #             docs = s.documents(path=str(path.resolve()))
# #             for d in docs:
# #                 return d.get("modified")
# #         return None

# #     def _current_mtime(self, path: Path) -> str:
# #         # return datetime.utcfromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
# #         return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


# #     def _needs_indexing(self, path: Path) -> bool:
# #         """Return True if file is new OR modified."""
# #         stored = self._indexed_mtime(path)
# #         current = self._current_mtime(path)
# #         return stored != current

# #     # ----------------------------------------------------------
# #     # INDEXING OPERATIONS
# #     # ----------------------------------------------------------
# #     def add_or_update(self, path: Path, content: str):
# #         writer = self.ix.writer()
# #         try:
# #             modified = self._current_mtime(path)
# #             size_b = path.stat().st_size

# #             writer.update_document(
# #                 path=str(path.resolve()),
# #                 filename=path.name,
# #                 filetype=path.suffix.lower().lstrip('.'),
# #                 modified=modified,
# #                 size_bytes=size_b,
# #                 content=content,
# #             )
# #             writer.commit()
# #             self._ensure_spellchecker()
# #         except Exception:
# #             try:
# #                 writer.cancel()
# #             except Exception:
# #                 pass

# #     # def index_folder(self, folder: str, allowed_exts: Optional[List[str]] = None):
# #     #     """
# #     #     Incremental indexing: only index new/modified files.
# #     #     """
# #     #     allowed = set([ext.lower() for ext in allowed_exts]) if allowed_exts else set(EXTRACTORS.keys())

# #     #     p = Path(folder)
# #     #     if not p.exists() or not p.is_dir():
# #     #         return 0

# #     #     count = 0
# #     #     for file in p.rglob("*"):
# #     #         if not file.is_file():
# #     #             continue

# #     #         suffix = file.suffix.lower()
# #     #         if suffix not in allowed:
# #     #             continue

# #     #         # 🔥 skip unchanged files
# #     #         if not self._needs_indexing(file):
# #     #             continue

# #     #         extractor = EXTRACTORS.get(suffix)
# #     #         if not extractor:
# #     #             continue

# #     #         try:
# #     #             content = extractor(file)
# #     #         except Exception:
# #     #             content = None

# #     #         if content:
# #     #             self.add_or_update(file, content)
# #     #             count += 1

# #     #     return count

# #     def index_folder(self, folder: str, allowed_exts: Optional[List[str]] = None):
# #         """
# #         Incremental indexing using a lightweight JSON metadata cache (path -> mtime iso).
# #         This avoids expensive per-file Whoosh lookups and speeds up re-index operations.
# #         """

# #         # Local import to avoid circular import at module load time
# #         try:
# #             from utils.storage_helper import read_index_meta, write_index_meta
# #         except Exception:
# #             # If someone runs this module standalone, fallback to no-cache behavior
# #             read_index_meta = lambda: {}
# #             write_index_meta = lambda meta: None

# #         allowed = set([ext.lower() for ext in allowed_exts]) if allowed_exts else set(EXTRACTORS.keys())

# #         p = Path(folder)
# #         if not p.exists() or not p.is_dir():
# #             return 0

# #         # load cache
# #         cache = read_index_meta() or {}
# #         cache_changed = False

# #         count = 0
# #         for file in p.rglob("*"):
# #             if not file.is_file():
# #                 continue

# #             suffix = file.suffix.lower()
# #             if suffix not in allowed:
# #                 continue

# #             # compute current mtime string
# #             try:
# #                 current_mtime = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
# #             except Exception:
# #                 # if stat fails, skip file
# #                 continue

# #             cached_mtime = cache.get(str(file))

# #             # Skip unchanged files quickly using cache
# #             if cached_mtime == current_mtime:
# #                 continue

# #             # Need to (re-)index — extract content
# #             extractor = EXTRACTORS.get(suffix)
# #             if not extractor:
# #                 continue

# #             try:
# #                 content = extractor(file)
# #             except Exception:
# #                 content = None

# #             if content:
# #                 try:
# #                     self.add_or_update(file, content)
# #                     count += 1
# #                     # update cache only after a successful index
# #                     cache[str(file)] = current_mtime
# #                     cache_changed = True
# #                 except Exception:
# #                     # indexing failed; leave cache untouched (so we retry next run)
# #                     pass

# #         # write back cache if changed
# #         if cache_changed:
# #             try:
# #                 write_index_meta(cache)
# #             except Exception:
# #                 pass

# #         return count

# #     # ----------------------------------------------------------
# #     # SEARCH HELPERS
# #     # ----------------------------------------------------------
# #     def _strip_html(self, text):
# #         return re.sub(r"<[^>]+>", "", text)
    
# #     def _format_snippet(self, hit, field="content"):
# #         raw = hit.highlights(field, top=5) or ""
# #         if not raw:
# #             txt = hit.get(field, "")[:200]
# #             cleaned = txt.replace("\n", " ").strip()
# #             return (cleaned + "...") if cleaned else ""

# #         # Clean into single line
# #         single = raw.replace("\n", " ")
# #         single = " ".join(single.split())

# #         # Strip any highlight HTML
# #         return self._strip_html(single)


# #     # def _format_snippet(self, hit, field="content"):
# #     #     raw = hit.highlights(field, top=1) or ""
# #     #     if not raw:
# #     #         txt = hit.get(field, "")[:200]
# #     #         return (txt.replace("\n", " ").strip() + "...") if txt else ""

# #     #     # Clean into single line
# #     #     single = raw.replace("\n", " ")
# #     #     single = " ".join(single.split())
# #     #     return single

# #     def _post_filter(self, docs, date_from=None, date_to=None, size_from_b=None, size_to_b=None, case_sensitive=False, whole_word=False, file_types=None):
# #         results = []
# #         for h in docs:
# #             try:
# #                 modified = h.get('modified')
# #                 size_b = h.get('size_kb') and int(h.get('size_kb') * 1024)
# #                 ftype = h.get('filetype')
# #             except Exception:
# #                 continue

# #             # Date filters
# #             if date_from or date_to:
# #                 try:
# #                     mod_dt = datetime.strptime(modified, "%Y-%m-%d %H:%M:%S")
# #                 except Exception:
# #                     continue

# #                 if date_from and mod_dt < date_from:
# #                     continue
# #                 if date_to and mod_dt > date_to:
# #                     continue

# #             # Size filters
# #             if size_from_b and (size_b is None or size_b < size_from_b):
# #                 continue
# #             if size_to_b and (size_b is None or size_b > size_to_b):
# #                 continue

# #             # File type filters
# #             if file_types and file_types != ["all"]:
# #                 if ftype.lower() not in [ft.lower() for ft in file_types]:
# #                     continue

# #             results.append(h)

# #         return results

# #     # ----------------------------------------------------------
# #     # FULL SEARCH PIPELINE
# #     # ----------------------------------------------------------
# #     def search(self, query: str, limit: int = 50,
# #                date_from=None, date_to=None,
# #                size_from_b=None, size_to_b=None,
# #                case_sensitive=False, whole_word=False,
# #                file_types=None):

# #         with self.ix.searcher() as searcher:
# #             parser = MultifieldParser(["content"], schema=self.ix.schema)

# #             q = parser.parse(query)
# #             hits = searcher.search(q, limit=limit)

# #             docs = []
# #             for h in hits:
# #                 docs.append({
# #                     'path': h.get('path'),
# #                     'filename': h.get('filename'),
# #                     'filetype': h.get('filetype'),
# #                     'modified': h.get('modified'),
# #                     'size_kb': int(h.get('size_bytes') / 1024) if h.get('size_bytes') else None,
# #                     'score': float(h.score),
# #                     'snippet': self._format_snippet(h),
# #                 })

# #             # --------------------------------------------------
# #             # SPELLING CORRECTION WHEN ZERO RESULTS
# #             # --------------------------------------------------
# #             if not docs and self.spell:
# #                 suggestions = []
# #                 for term in query.split():
# #                     try:
# #                         s = self.spell.suggest(term)
# #                         if s:
# #                             suggestions.extend(s[:1])
# #                     except Exception:
# #                         pass

# #                 if suggestions:
# #                     sug_q = " | ".join([f'"{s}"' for s in suggestions])
# #                     try:
# #                         sq = parser.parse(sug_q)
# #                         sh = searcher.search(sq, limit=limit)
# #                         for h in sh:
# #                             docs.append({
# #                                 'path': h.get('path'),
# #                                 'filename': h.get('filename'),
# #                                 'filetype': h.get('filetype'),
# #                                 'modified': h.get('modified'),
# #                                 'size_kb': int(h.get('size_bytes') / 1024),
# #                                 'score': float(h.score),
# #                                 'snippet': self._format_snippet(h),
# #                             })
# #                     except Exception:
# #                         pass

# #             # FINAL FILTERING
# #             filtered = self._post_filter(
# #                 docs,
# #                 date_from=date_from,
# #                 date_to=date_to,
# #                 size_from_b=size_from_b,
# #                 size_to_b=size_to_b,
# #                 case_sensitive=case_sensitive,
# #                 whole_word=whole_word,
# #                 file_types=file_types,
# #             )

# #             return filtered



# import re
# from whoosh import index as whoosh_index
# from whoosh.fields import Schema, TEXT, ID, NUMERIC
# from whoosh.analysis import StemmingAnalyzer
# from whoosh.qparser import MultifieldParser
# from whoosh.spelling import Corrector
# from pathlib import Path
# from datetime import datetime
# from typing import Optional, List
# from .whoosh_extractors import EXTRACTORS
# import os

# # ----------------------------------------------------------
# # WATCHDOG (for real-time updates)
# # ----------------------------------------------------------
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler


# class IndexWatcher(FileSystemEventHandler):
#     def __init__(self, indexer, folder):
#         self.indexer = indexer
#         self.folder = Path(folder)

#     def on_created(self, event):
#         if event.is_directory:
#             return
#         path = Path(event.src_path)
#         print(f"[watcher] created: {path}")

#         extractor = EXTRACTORS.get(path.suffix.lower())
#         if not extractor:
#             return

#         content = extractor(path)
#         if content:
#             self.indexer.add_or_update(path, content)

#     def on_modified(self, event):
#         if event.is_directory:
#             return
#         path = Path(event.src_path)
#         print(f"[watcher] modified: {path}")

#         extractor = EXTRACTORS.get(path.suffix.lower())
#         if not extractor:
#             return

#         content = extractor(path)
#         if content:
#             self.indexer.add_or_update(path, content)

#     def on_deleted(self, event):
#         if event.is_directory:
#             return
#         path = Path(event.src_path)
#         print(f"[watcher] deleted: {path}")
#         # Optional: delete from index


# def start_watcher(indexer, folder: str):
#     """Start live watcher on the folder."""
#     print(f"[watcher] Starting real-time watcher on: {folder}")

#     handler = IndexWatcher(indexer, folder)
#     observer = Observer()
#     observer.schedule(handler, folder, recursive=True)
#     observer.start()
#     return observer


# # =====================================================================
# #    WHOOSH INDEXER CLASS (your full code, unchanged except watcher)
# # =====================================================================
# class WhooshIndexer:
#     def __init__(self, index_dir: str):
#         self.index_dir = Path(index_dir)
#         self.schema = self._get_schema()
#         self.ix = self._open_or_create()
#         self.spell = None
#         self._ensure_spellchecker()

#     def _get_schema(self):
#         return Schema(
#             path=ID(stored=True, unique=True),
#             filename=TEXT(stored=True, analyzer=StemmingAnalyzer()),
#             filetype=ID(stored=True),
#             modified=ID(stored=True),
#             size_bytes=NUMERIC(stored=True),
#             content=TEXT(stored=True, analyzer=StemmingAnalyzer()),
#         )

#     def _open_or_create(self):
#         if not self.index_dir.exists():
#             self.index_dir.mkdir(parents=True, exist_ok=True)

#         if whoosh_index.exists_in(str(self.index_dir)):
#             return whoosh_index.open_dir(str(self.index_dir))

#         return whoosh_index.create_in(str(self.index_dir), self.schema)

#     def _ensure_spellchecker(self):
#         try:
#             self.spell = Corrector(self.ix.reader(), fieldname='content')
#         except Exception:
#             self.spell = None

#     def _indexed_mtime(self, path: Path) -> Optional[str]:
#         with self.ix.searcher() as s:
#             docs = s.documents(path=str(path.resolve()))
#             for d in docs:
#                 return d.get("modified")
#         return None

#     def _current_mtime(self, path: Path) -> str:
#         return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")

#     def _needs_indexing(self, path: Path) -> bool:
#         stored = self._indexed_mtime(path)
#         current = self._current_mtime(path)
#         return stored != current

#     def add_or_update(self, path: Path, content: str):
#         writer = self.ix.writer()
#         try:
#             modified = self._current_mtime(path)
#             size_b = path.stat().st_size

#             writer.update_document(
#                 path=str(path.resolve()),
#                 filename=path.name,
#                 filetype=path.suffix.lower().lstrip('.'),
#                 modified=modified,
#                 size_bytes=size_b,
#                 content=content,
#             )
#             writer.commit()
#             self._ensure_spellchecker()
#         except Exception:
#             try:
#                 writer.cancel()
#             except Exception:
#                 pass

#     # ----------------------------------------------------------
#     # UPDATED index_folder (with watcher)
#     # ----------------------------------------------------------
#     def index_folder(self, folder: str, allowed_exts: Optional[List[str]] = None):
#         """
#         Incremental indexing with optional REAL-TIME watcher based on .env flag.
#         Only modified/new files indexed. Watcher handles future changes.
#         """

#         from config.settings import settings
#         watcher_enabled = settings.ENABLE_WATCHER

#         try:
#             from utils.storage_helper import read_index_meta, write_index_meta
#         except Exception:
#             read_index_meta = lambda: {}
#             write_index_meta = lambda meta: None

#         allowed = set([ext.lower() for ext in allowed_exts]) if allowed_exts else set(EXTRACTORS.keys())
#         p = Path(folder)
#         if not p.exists() or not p.is_dir():
#             return 0

#         cache = read_index_meta() or {}
#         cache_changed = False
#         count = 0

#         # First pass: incremental indexing
#         for file in p.rglob("*"):
#             if not file.is_file():
#                 continue

#             suffix = file.suffix.lower()
#             if suffix not in allowed:
#                 continue

#             try:
#                 current_mtime = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
#             except Exception:
#                 continue

#             cached_mtime = cache.get(str(file))

#             if cached_mtime == current_mtime:
#                 continue

#             extractor = EXTRACTORS.get(suffix)
#             if not extractor:
#                 continue

#             try:
#                 content = extractor(file)
#             except Exception:
#                 content = None

#             if content:
#                 try:
#                     self.add_or_update(file, content)
#                     cache[str(file)] = current_mtime
#                     cache_changed = True
#                     count += 1
#                 except Exception:
#                     pass

#         with self.ix.writer() as writer:
#             for stored_path in list(cache.keys()):
#                 if not Path(stored_path).exists():
#                     writer.delete_by_term("path", stored_path)
#                     del cache[stored_path]
#                     cache_changed = True

#         if cache_changed:
#             write_index_meta(cache)

#         # Start watcher only ONCE
#         if watcher_enabled:
#             print(f"[watcher] ENABLE_WATCHER = true → watching {folder}")
#             self.start_watcher(folder)
#         else:
#             print("[watcher] ENABLE_WATCHER = false → skipping watcher")

#         return count

#     # Required for index_folder() to work
#     def start_watcher(self, folder: str):
#         return start_watcher(self, folder)

#     # ----------------------------------------------------------
#     # SEARCH PIPELINE (unchanged)
#     # ----------------------------------------------------------
#     def _strip_html(self, text):
#         return re.sub(r"<[^>]+>", "", text)

#     def _format_snippet(self, hit, field="content"):
#         raw = hit.highlights(field, top=5) or ""
#         if not raw:
#             txt = hit.get(field, "")[:200]
#             cleaned = txt.replace("\n", " ").strip()
#             return (cleaned + "...") if cleaned else ""

#         single = raw.replace("\n", " ")
#         single = " ".join(single.split())
#         return self._strip_html(single)

#     def _post_filter(self, docs, date_from=None, date_to=None,
#                      size_from_b=None, size_to_b=None,
#                      case_sensitive=False, whole_word=False,
#                      file_types=None):

#         results = []
#         for h in docs:
#             try:
#                 modified = h.get('modified')
#                 size_b = h.get('size_kb') and int(h.get('size_kb') * 1024)
#                 ftype = h.get('filetype')
#             except Exception:
#                 continue

#             if date_from or date_to:
#                 try:
#                     mod_dt = datetime.strptime(modified, "%Y-%m-%d %H:%M:%S")
#                 except Exception:
#                     continue
#                 if date_from and mod_dt < date_from:
#                     continue
#                 if date_to and mod_dt > date_to:
#                     continue

#             if size_from_b and (size_b is None or size_b < size_from_b):
#                 continue
#             if size_to_b and (size_b is None or size_b > size_to_b):
#                 continue

#             if file_types and file_types != ["all"]:
#                 if ftype.lower() not in [ft.lower() for ft in file_types]:
#                     continue

#             results.append(h)

#         return results

#     def search(self, query: str, limit: int = 50,
#                date_from=None, date_to=None,
#                size_from_b=None, size_to_b=None,
#                case_sensitive=False, whole_word=False,
#                file_types=None):

#         with self.ix.searcher() as searcher:
#             parser = MultifieldParser(["content"], schema=self.ix.schema)
#             q = parser.parse(query)
#             hits = searcher.search(q, limit=limit)

#             docs = []
#             for h in hits:
#                 docs.append({
#                     'path': h.get('path'),
#                     'filename': h.get('filename'),
#                     'filetype': h.get('filetype'),
#                     'modified': h.get('modified'),
#                     'size_kb': int(h.get('size_bytes') / 1024) if h.get('size_bytes') else None,
#                     'score': float(h.score),
#                     'snippet': self._format_snippet(h),
#                 })

#             # Spell suggestions
#             if not docs and self.spell:
#                 suggestions = []
#                 for term in query.split():
#                     try:
#                         s = self.spell.suggest(term)
#                         if s:
#                             suggestions.append(s[0])
#                     except Exception:
#                         pass

#                 if suggestions:
#                     sug_q = " | ".join([f'"{s}"' for s in suggestions])
#                     try:
#                         sq = parser.parse(sug_q)
#                         sh = searcher.search(sq, limit=limit)
#                         for h in sh:
#                             docs.append({
#                                 'path': h.get('path'),
#                                 'filename': h.get('filename'),
#                                 'filetype': h.get('filetype'),
#                                 'modified': h.get('modified'),
#                                 'size_kb': int(h.get('size_bytes') / 1024),
#                                 'score': float(h.score),
#                                 'snippet': self._format_snippet(h),
#                             })
#                     except Exception:
#                         pass

#             filtered = self._post_filter(
#                 docs,
#                 date_from=date_from,
#                 date_to=date_to,
#                 size_from_b=size_from_b,
#                 size_to_b=size_to_b,
#                 case_sensitive=case_sensitive,
#                 whole_word=whole_word,
#                 file_types=file_types,
#             )

#             return filtered



import re
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from whoosh import index as whoosh_index
from whoosh.fields import Schema, TEXT, ID, NUMERIC
from whoosh.analysis import StemmingAnalyzer
from whoosh.qparser import MultifieldParser
from whoosh.spelling import Corrector

from .whoosh_extractors import EXTRACTORS

# -------------------------------
# Watchdog imports (for watcher)
# -------------------------------
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# ============================================================
# Watchdog Event Handler
# ============================================================
# class IndexWatcher(FileSystemEventHandler):
#     def __init__(self, indexer, folder):
#         self.indexer = indexer
#         self.folder = Path(folder)

#     def on_created(self, event):
#         if event.is_directory:
#             return
#         path = Path(event.src_path)
#         print(f"[watcher] created: {path}")

#         extractor = EXTRACTORS.get(path.suffix.lower())
#         if extractor:
#             content = extractor(path)
#             if content:
#                 self.indexer.add_or_update(path, content)

#     def on_modified(self, event):
#         if event.is_directory:
#             return
#         path = Path(event.src_path)
#         print(f"[watcher] modified: {path}")

#         extractor = EXTRACTORS.get(path.suffix.lower())
#         if extractor:
#             content = extractor(path)
#             if content:
#                 self.indexer.add_or_update(path, content)

#     def on_deleted(self, event):
#         if event.is_directory:
#             return

#         path = Path(event.src_path)
#         print(f"[watcher] deleted: {path}")

#         try:
#             writer = self.indexer.ix.writer()
#             writer.delete_by_term("path", str(path.resolve()))
#             writer.commit()
#             print(f"[watcher] removed from index: {path}")

#             # also update cache
#             from utils.storage_helper import read_index_meta, write_index_meta
#             cache = read_index_meta()
#             if str(path) in cache:
#                 cache.pop(str(path), None)
#                 write_index_meta(cache)

#         except Exception as e:
#             print(f"[watcher] failed to delete {path}: {e}")

# ----------------------------------------------------------
# WATCHDOG (Real-time updates with JSON sync)
# ----------------------------------------------------------
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils.storage_helper import read_index_meta, write_index_meta


class IndexWatcher(FileSystemEventHandler):
    def __init__(self, indexer, folder):
        self.indexer = indexer
        self.folder = Path(folder)

    def _update_cache(self, path: Path):
        """Update index_meta.json when file is added or modified."""
        cache = read_index_meta() or {}
        current_mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        cache[str(path)] = current_mtime
        write_index_meta(cache)

    def _remove_from_cache(self, path: Path):
        """Remove deleted files from index_meta.json."""
        cache = read_index_meta() or {}
        path_str = str(path)
        if path_str in cache:
            del cache[path_str]
            write_index_meta(cache)

    # ---------------------------
    # FILE CREATED
    # ---------------------------
    def on_created(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)
        print(f"[watcher] created: {path}")

        extractor = EXTRACTORS.get(path.suffix.lower())
        if not extractor:
            return

        content = extractor(path)
        if content:
            self.indexer.add_or_update(path, content)
            self._update_cache(path)

    # ---------------------------
    # FILE MODIFIED
    # ---------------------------
    def on_modified(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)
        print(f"[watcher] modified: {path}")

        extractor = EXTRACTORS.get(path.suffix.lower())
        if not extractor:
            return

        content = extractor(path)
        if content:
            self.indexer.add_or_update(path, content)
            self._update_cache(path)

    # ---------------------------
    # FILE DELETED
    # ---------------------------
    def on_deleted(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)
        print(f"[watcher] deleted: {path}")

        # Remove from Whoosh index
        writer = self.indexer.ix.writer()
        writer.delete_by_term("path", str(path))
        writer.commit()

        # Remove from JSON cache
        self._remove_from_cache(path)

def start_watcher(indexer, folder: str):
    print(f"[watcher] Starting real-time watcher on: {folder}")

    handler = IndexWatcher(indexer, folder)
    observer = Observer()
    observer.schedule(handler, folder, recursive=True)
    observer.start()
    return observer


# ============================================================
# WHOOSH INDEXER CLASS
# ============================================================
class WhooshIndexer:
    _watcher_started = False   # ensures watcher doesn't start multiple times

    def __init__(self, index_dir: str):
        self.index_dir = Path(index_dir)
        self.schema = self._get_schema()
        self.ix = self._open_or_create()
        self.spell = None
        self._ensure_spellchecker()

    # -------------------------------
    # Schema
    # -------------------------------
    def _get_schema(self):
        return Schema(
            path=ID(stored=True, unique=True),
            filename=TEXT(stored=True, analyzer=StemmingAnalyzer()),
            filetype=ID(stored=True),
            modified=ID(stored=True),
            size_bytes=NUMERIC(stored=True),
            content=TEXT(stored=True, analyzer=StemmingAnalyzer()),
        )

    # -------------------------------
    # Index creation / loading
    # -------------------------------
    def _open_or_create(self):
        if not self.index_dir.exists():
            self.index_dir.mkdir(parents=True, exist_ok=True)

        if whoosh_index.exists_in(str(self.index_dir)):
            return whoosh_index.open_dir(str(self.index_dir))

        return whoosh_index.create_in(str(self.index_dir), self.schema)

    def _ensure_spellchecker(self):
        try:
            self.spell = Corrector(self.ix.reader(), fieldname="content")
        except Exception:
            self.spell = None

    # -------------------------------
    # Compare mtimes
    # -------------------------------
    def _indexed_mtime(self, path: Path) -> Optional[str]:
        with self.ix.searcher() as s:
            docs = s.documents(path=str(path.resolve()))
            for d in docs:
                return d.get("modified")
        return None

    def _current_mtime(self, path: Path) -> str:
        return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")

    def _needs_indexing(self, path: Path) -> bool:
        stored = self._indexed_mtime(path)
        current = self._current_mtime(path)
        return stored != current

    # -------------------------------
    # Add or update document
    # -------------------------------
    def add_or_update(self, path: Path, content: str):
        writer = self.ix.writer()
        try:
            modified = self._current_mtime(path)
            size_b = path.stat().st_size

            writer.update_document(
                path=str(path.resolve()),
                filename=path.name,
                filetype=path.suffix.lower().lstrip("."),
                modified=modified,
                size_bytes=size_b,
                content=content,
            )
            writer.commit()
            self._ensure_spellchecker()
        except Exception:
            writer.cancel()

    # ============================================================
    # Incremental indexer with deletion cleanup + watcher support
    # ============================================================
    def index_folder(self, folder: str, allowed_exts: Optional[List[str]] = None):
        from config.settings import settings
        watcher_enabled = settings.ENABLE_WATCHER

        # cache utils
        try:
            from utils.storage_helper import read_index_meta, write_index_meta
        except Exception:
            read_index_meta = lambda: {}
            write_index_meta = lambda meta: None

        allowed = set([ext.lower() for ext in allowed_exts]) if allowed_exts else set(EXTRACTORS.keys())

        p = Path(folder)
        if not p.exists() or not p.is_dir():
            return 0

        cache = read_index_meta() or {}
        cache_changed = False
        count = 0

        # -------------------------------------
        # PHASE 1 — Index new and modified files
        # -------------------------------------
        for file in p.rglob("*"):
            if not file.is_file():
                continue

            suffix = file.suffix.lower()
            if suffix not in allowed:
                continue

            try:
                current_mtime = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                continue

            cached_mtime = cache.get(str(file))

            # skip unchanged
            if cached_mtime == current_mtime:
                continue

            extractor = EXTRACTORS.get(suffix)
            if not extractor:
                continue

            content = None
            try:
                content = extractor(file)
            except Exception:
                pass

            if content:
                self.add_or_update(file, content)
                cache[str(file)] = current_mtime
                cache_changed = True
                count += 1

        # -------------------------------------
        # PHASE 2 — REMOVE deleted files from index
        # -------------------------------------
        actual_files = {str(f.resolve()) for f in p.rglob("*") if f.is_file()}
        cached_files = set(cache.keys())

        deleted_files = cached_files - actual_files
        if deleted_files:
            writer = self.ix.writer()
            for del_path in deleted_files:
                try:
                    writer.delete_by_term("path", del_path)
                    cache.pop(del_path, None)
                    print(f"[cleanup] removed missing file: {del_path}")
                except Exception as e:
                    print(f"[cleanup] failed to remove {del_path}: {e}")
            writer.commit()
            cache_changed = True

        if cache_changed:
            write_index_meta(cache)

        # -------------------------------------
        # PHASE 3 — Start watcher if enabled
        # -------------------------------------
        if watcher_enabled and not WhooshIndexer._watcher_started:
            WhooshIndexer._watcher_started = True
            print(f"[watcher] ENABLE_WATCHER=true → watching {folder}")
            start_watcher(self, folder)
        elif not watcher_enabled:
            print("[watcher] ENABLE_WATCHER=false → watcher disabled")

        return count

    # -------------------------------
    # Search API
    # -------------------------------
    def _strip_html(self, text):
        return re.sub(r"<[^>]+>", "", text)

    def _format_snippet(self, hit, field="content"):
        raw = hit.highlights(field, top=5) or ""
        if not raw:
            txt = hit.get(field, "")[:200]
            cleaned = txt.replace("\n", " ").strip()
            return cleaned + "..." if cleaned else ""

        cleaned = " ".join(raw.replace("\n", " ").split())
        return self._strip_html(cleaned)

    def _post_filter(self, docs, date_from=None, date_to=None,
                     size_from_b=None, size_to_b=None,
                     case_sensitive=False, whole_word=False,
                     file_types=None):

        results = []
        for h in docs:
            try:
                modified = h.get("modified")
                size_b = h.get("size_kb") and int(h.get("size_kb") * 1024)
                ftype = h.get("filetype")
            except Exception:
                continue

            # date filter
            if date_from or date_to:
                try:
                    mod_dt = datetime.strptime(modified, "%Y-%m-%d %H:%M:%S")
                except:
                    continue
                if date_from and mod_dt < date_from:
                    continue
                if date_to and mod_dt > date_to:
                    continue

            # size filter
            if size_from_b and (size_b is None or size_b < size_from_b):
                continue
            if size_to_b and (size_b is None or size_b > size_to_b):
                continue

            # type filter
            if file_types and file_types != ["all"]:
                if ftype.lower() not in [ft.lower() for ft in file_types]:
                    continue

            results.append(h)

        return results

    def search(self, query: str, limit: int = 50,
               date_from=None, date_to=None,
               size_from_b=None, size_to_b=None,
               case_sensitive=False, whole_word=False,
               file_types=None):

        with self.ix.searcher() as searcher:
            parser = MultifieldParser(["content"], schema=self.ix.schema)
            q = parser.parse(query)
            hits = searcher.search(q, limit=limit)

            docs = []
            for h in hits:
                docs.append({
                    "path": h.get("path"),
                    "filename": h.get("filename"),
                    "filetype": h.get("filetype"),
                    "modified": h.get("modified"),
                    "size_kb": int(h.get("size_bytes") / 1024) if h.get("size_bytes") else None,
                    "score": float(h.score),
                    "snippet": self._format_snippet(h),
                })

            # Spell correction when no result
            if not docs and self.spell:
                suggestions = []
                for term in query.split():
                    try:
                        s = self.spell.suggest(term)
                        if s:
                            suggestions.append(s[0])
                    except:
                        pass

                if suggestions:
                    sug_q = " | ".join([f'"{s}"' for s in suggestions])
                    try:
                        sq = parser.parse(sug_q)
                        sh = searcher.search(sq, limit=limit)
                        for h in sh:
                            docs.append({
                                "path": h.get("path"),
                                "filename": h.get("filename"),
                                "filetype": h.get("filetype"),
                                "modified": h.get("modified"),
                                "size_kb": int(h.get("size_bytes") / 1024),
                                "score": float(h.score),
                                "snippet": self._format_snippet(h),
                            })
                    except:
                        pass

            filtered = self._post_filter(
                docs,
                date_from=date_from,
                date_to=date_to,
                size_from_b=size_from_b,
                size_to_b=size_to_b,
                case_sensitive=case_sensitive,
                whole_word=whole_word,
                file_types=file_types,
            )

            return filtered
            
