from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.projects import ProjectStatusValue, ShareOut
from app.schemas.resources import ResourceTypeValue


class ShareStateOut(BaseModel):
    enabled: bool
    share: ShareOut | None


class ShareMutationOut(BaseModel):
    enabled: bool
    share: ShareOut


class PublicPortalProjectOut(BaseModel):
    name: str
    status: ProjectStatusValue


class PublicPortalVersionOut(BaseModel):
    version_number: int
    name: str
    release_notes: str
    overview: str | None
    published_at: datetime


class PublicVersionRefOut(BaseModel):
    version_number: int
    published_at: datetime


class PublicFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    mime_type: str
    size_bytes: int
    created_at: datetime


class PublicResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    url: str
    type: ResourceTypeValue
    description: str | None
    position: int


class PublicPortalOut(BaseModel):
    project: PublicPortalProjectOut
    version: PublicPortalVersionOut
    resources: list[PublicResourceOut]
    files: list[PublicFileOut]
    versions_available: list[PublicVersionRefOut]


class PublicDownloadRequest(BaseModel):
    version_number: int | None = Field(default=None, ge=1)
