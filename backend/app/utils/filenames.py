import re


def safe_filename(name: str) -> str:
    """Normalize a display filename into a storage-safe basename."""
    cleaned = name.strip().replace("\\", "/")
    cleaned = cleaned.split("/")[-1]
    cleaned = re.sub(r"[^\w.\- ()\[\]]+", "_", cleaned, flags=re.UNICODE)
    cleaned = cleaned.strip(" ._")
    if not cleaned:
        cleaned = "file"
    return cleaned[:200]
