"""Version / publish request and response schemas (V2)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.limits import RELEASE_NOTES_MAX
from app.schemas.projects import ShareOut
from app.schemas.resources import ResourceTypeValue


class PublishRequest(BaseModel):
    release_notes: str = Field(min_length=1, max_length=RELEASE_NOTES_MAX)

    @field_validator("release_notes", mode="before")
    @classmethod
    def trim_release_notes(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Release notes are required")
        return cleaned


class VersionSummaryOut(BaseModel):
    id: UUID
    project_id: UUID
    version_number: int
    name: str
    release_notes: str
    overview: str | None
    published_at: datetime


class VersionOut(BaseModel):
    id: UUID
    project_id: UUID
    version_number: int
    name: str
    release_notes: str
    overview: str | None
    published_at: datetime
    published_by_user_id: UUID


class VersionFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    mime_type: str
    size_bytes: int
    created_at: datetime


class VersionResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    url: str
    type: ResourceTypeValue
    description: str | None
    position: int


class PublishResultOut(BaseModel):
    version: VersionOut
    files: list[VersionFileOut]
    resources: list[VersionResourceOut]
    share: ShareOut


class VersionDetailOut(BaseModel):
    version: VersionOut
    files: list[VersionFileOut]
    resources: list[VersionResourceOut]
