"""Draft overview / files / resources request and response schemas (V2)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.limits import (
    DRAFT_FILE_NAME_MAX,
    OVERVIEW_MAX,
)
from app.schemas.resources import ResourceTypeValue, _validate_http_url


class DraftUpdateRequest(BaseModel):
    overview: str | None = Field(default=None, max_length=OVERVIEW_MAX)

    @field_validator("overview", mode="before")
    @classmethod
    def normalize_overview(cls, value: object) -> object:
        if value is None or not isinstance(value, str):
            return value
        cleaned = value.strip()
        return cleaned or None


class DraftOut(BaseModel):
    overview: str | None
    updated_at: datetime
    has_unpublished_changes: bool


class DraftSummaryOut(BaseModel):
    overview: str | None
    updated_at: datetime
    has_unpublished_changes: bool
    file_count: int
    resource_count: int


class DraftFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    mime_type: str
    size_bytes: int
    created_at: datetime


class DraftUploadUrlRequest(BaseModel):
    name: str = Field(min_length=1, max_length=DRAFT_FILE_NAME_MAX)
    mime_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(ge=1)


class DraftConfirmUploadRequest(BaseModel):
    token: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=DRAFT_FILE_NAME_MAX)
    mime_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(ge=1)


class DraftUploadUrlOut(BaseModel):
    upload_url: str
    token: str
    expires_at: datetime


class DownloadUrlOut(BaseModel):
    download_url: str
    expires_at: datetime
    name: str


class DraftResourceCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    url: str = Field(min_length=1, max_length=2048)
    type: ResourceTypeValue
    description: str | None = Field(default=None, max_length=2000)
    position: int | None = Field(default=None, ge=0)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Title is required")
        return cleaned

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return _validate_http_url(value)

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, value: object) -> object:
        if value is None or not isinstance(value, str):
            return value
        cleaned = value.strip()
        return cleaned or None


class DraftResourceUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    url: str | None = Field(default=None, min_length=1, max_length=2048)
    type: ResourceTypeValue | None = None
    description: str | None = Field(default=None, max_length=2000)
    position: int | None = Field(default=None, ge=0)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: object) -> object:
        if value is None or not isinstance(value, str):
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Title is required")
        return cleaned

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, value: object) -> object:
        if value is None or not isinstance(value, str):
            return value
        return _validate_http_url(value)

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, value: object) -> object:
        if value is None or not isinstance(value, str):
            return value
        cleaned = value.strip()
        return cleaned or None


class DraftResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    title: str
    url: str
    type: ResourceTypeValue
    description: str | None
    position: int
    created_at: datetime
    updated_at: datetime
