"""Normative V2 field and upload limits (docs/v2 PRD / Data Model / API Contract)."""

# Text fields
PROJECT_NAME_MAX = 120
DISPLAY_NAME_MAX = 80
OVERVIEW_MAX = 10_000
RELEASE_NOTES_MAX = 10_000
RESOURCE_TITLE_MAX = 120
RESOURCE_URL_MAX = 2048
RESOURCE_DESCRIPTION_MAX = 2000

# Draft files
DRAFT_FILE_MAX_BYTES = 26_214_400  # 25 MiB
DRAFT_FILES_MAX_PER_PROJECT = 50
DRAFT_FILE_NAME_MAX = 255
STORAGE_PATH_MAX = 1024

DRAFT_FILE_MIME_ALLOWLIST: frozenset[str] = frozenset(
    {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/gif",
        "application/zip",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
    }
)
