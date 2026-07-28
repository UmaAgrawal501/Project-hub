from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.limits import OVERVIEW_MAX, PROJECT_NAME_MAX
from app.schemas.draft import DraftSummaryOut


class ProjectStatusValue(str, Enum):
    active = "active"
    completed = "completed"
    archived = "archived"


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=PROJECT_NAME_MAX)
    overview: str | None = Field(default=None, max_length=OVERVIEW_MAX)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name is required")
        return cleaned

    @field_validator("overview", mode="before")
    @classmethod
    def normalize_overview(cls, value: object) -> object:
        if value is None or not isinstance(value, str):
            return value
        cleaned = value.strip()
        return cleaned or None


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=PROJECT_NAME_MAX)
    status: ProjectStatusValue | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        if value is None or not isinstance(value, str):
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Name is required")
        return cleaned


class ShareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    version_number: int
    token: str
    is_enabled: bool
    public_path: str
    created_at: datetime
    updated_at: datetime


class ProjectSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    status: ProjectStatusValue
    created_at: datetime
    updated_at: datetime
    latest_version_number: int | None
    has_unpublished_changes: bool


class ProjectDetailOut(ProjectSummaryOut):
    draft: DraftSummaryOut
    share: ShareOut | None = None


class ProjectListMeta(BaseModel):
    limit: int
    offset: int
    total: int
