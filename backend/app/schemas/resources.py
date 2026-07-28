from enum import Enum
from urllib.parse import urlparse


class ResourceTypeValue(str, Enum):
    github = "github"
    figma = "figma"
    production = "production"
    staging = "staging"
    api_docs = "api_docs"
    postman = "postman"
    database_diagram = "database_diagram"
    drive = "drive"
    other = "other"


def _validate_http_url(value: str) -> str:
    url = value.strip()
    if len(url) > 2048:
        raise ValueError("URL must be at most 2048 characters")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Must be an http or https URL")
    if not parsed.netloc or not parsed.hostname:
        raise ValueError("URL must include a host")
    return url
