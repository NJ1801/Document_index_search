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

    return " ".join(parts).strip()
