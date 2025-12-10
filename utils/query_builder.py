# from models.search_models import SearchInput
# from typing import List, Optional

# def normalize_extensions(exts: List[str]):
#     norm = []
#     for e in exts:
#         if not e:
#             continue
#         e = e.lower().lstrip('.')
#         if e:
#             norm.append(e)
#     return norm

# def build_everything_query(data: SearchInput, folders: Optional[List[str]] = None) -> str:
#     parts = []

#     # Flags
#     if not data.case_sensitive:
#         parts.append("nocase:")
#     if not data.whole_word:
#         parts.append("nowholeword:")
#     if not data.case_sensitive:
#         parts.append("nodiacritics:")

#     # Folders
#     if folders:
#         folder_filters = " | ".join([f'"{f}\\*"' for f in folders])
#         parts.append(folder_filters)

#     # Keywords -> split by comma
#     terms = [t.strip() for t in data.keyword.split(',') if t.strip()]
#     if len(terms) == 1:
#         kw = terms[0].replace('"', '\\"')
#         parts.append(f'"{kw}"')
#     else:
#         escaped_terms = []
#         for t in terms:
#             escaped = t.replace('"', '\\"')
#             escaped_terms.append(f'"{escaped}"')
#         kws = " | ".join(escaped_terms)
#         parts.append(f'({kws})')

#     # File type filters
#     if data.file_types and data.file_types != ["all"]:
#         normalized = normalize_extensions(data.file_types)
#         if normalized:
#             ext_filters = " | ".join([f"ext:{ext}" for ext in normalized])
#             parts.append(ext_filters)

#     # Date filters
#     if data.date_from:
#         parts.append(f"dm:>{data.date_from}")
#     if data.date_to:
#         parts.append(f"dm:<{data.date_to}")

#     # if data.date_from and data.date_to:
#     #     parts.append(f"dm:{data.date_from}..{data.date_to}")

#     # elif data.date_from:
#     #     parts.append(f"dm:>={data.date_from}")

#     # elif data.date_to:
#     #     parts.append(f"dm:<={data.date_to}")


#     # Size filters (KB -> bytes)
#     if data.size_from is not None:
#         try:
#             size_from_b = int(float(data.size_from) * 1024)
#             parts.append(f"size:>{size_from_b}")
#         except Exception:
#             pass
#     if data.size_to is not None:
#         try:
#             size_to_b = int(float(data.size_to) * 1024)
#             parts.append(f"size:<{size_to_b}")
#         except Exception:
#             pass

#     return " ".join(parts).strip()


from models.search_models import SearchInput
from typing import List, Optional

def normalize_extensions(exts: List[str]):
    norm = []
    for e in exts:
        if not e:
            continue
        e = e.lower().lstrip('.')
        if e:
            norm.append(e)
    return norm


def build_everything_query(data: SearchInput, folders: Optional[List[str]] = None) -> str:
    """
    IMPORTANT:
    Everything.exe MUST NOT receive date filters or size filters,
    because it treats all date-only values as 00:00:00 (midnight)
    and will exclude same-day files.

    Date + size filters are handled COMPLETELY in Python-side SearchEngine.
    """

    parts = []

    # -------------------------------------------------------------------
    # FLAGS: nocase, whole-word, diacritics
    # -------------------------------------------------------------------
    if not data.case_sensitive:
        parts.append("nocase:")
    if not data.whole_word:
        parts.append("nowholeword:")
    if not data.case_sensitive:
        parts.append("nodiacritics:")

    # -------------------------------------------------------------------
    # FOLDERS
    # -------------------------------------------------------------------
    if folders:
        folder_filters = " | ".join([f'"{f}\\*"' for f in folders])
        parts.append(folder_filters)

    # -------------------------------------------------------------------
    # KEYWORDS (split by comma)
    # -------------------------------------------------------------------
    terms = [t.strip() for t in data.keyword.split(',') if t.strip()]

    if len(terms) == 1:
        kw = terms[0].replace('"', '\\"')
        parts.append(f'"{kw}"')
    else:
        escaped_terms = []
        for t in terms:
            escaped = t.replace('"', '\\"')
            escaped_terms.append(f'"{escaped}"')
        kws = " | ".join(escaped_terms)
        parts.append(f'({kws})')

    # -------------------------------------------------------------------
    # FILE TYPES
    # -------------------------------------------------------------------
    if data.file_types and data.file_types != ["all"]:
        normalized = normalize_extensions(data.file_types)
        if normalized:
            ext_filters = " | ".join([f"ext:{ext}" for ext in normalized])
            parts.append(ext_filters)

    # -------------------------------------------------------------------
    # ❌ REMOVE DATE FILTERS (handled entirely in Python)
    # -------------------------------------------------------------------
    # (DO NOT ADD ANY OF THESE)
    # dm:>YYYY-MM-DD
    # dm:<YYYY-MM-DD
    # dm:YYYY-MM-DD..YYYY-MM-DD

    # -------------------------------------------------------------------
    # ❌ REMOVE SIZE FILTERS (handled entirely in Python)
    # -------------------------------------------------------------------
    # (DO NOT ADD size:> or size:< to Everything query)

    return " ".join(parts).strip()
