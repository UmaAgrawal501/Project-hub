from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import ProjectVersion, VersionFile, VersionResource


class VersionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_project(self, *, project_id: UUID) -> list[ProjectVersion]:
        return (
            self.db.query(ProjectVersion)
            .filter(ProjectVersion.project_id == project_id)
            .order_by(ProjectVersion.version_number.desc())
            .all()
        )

    def get_by_number(
        self, *, project_id: UUID, version_number: int
    ) -> ProjectVersion | None:
        return (
            self.db.query(ProjectVersion)
            .filter(
                ProjectVersion.project_id == project_id,
                ProjectVersion.version_number == version_number,
            )
            .one_or_none()
        )

    def max_version_number(self, *, project_id: UUID) -> int | None:
        """Return max version_number for project (caller should lock the project row)."""
        return (
            self.db.query(func.max(ProjectVersion.version_number))
            .filter(ProjectVersion.project_id == project_id)
            .scalar()
        )

    def create_version(
        self,
        *,
        project_id: UUID,
        version_number: int,
        name: str,
        release_notes: str,
        overview: str | None,
        published_at: datetime,
        published_by_user_id: UUID,
    ) -> ProjectVersion:
        row = ProjectVersion(
            id=uuid4(),
            project_id=project_id,
            version_number=version_number,
            name=name,
            release_notes=release_notes,
            overview=overview,
            published_at=published_at,
            published_by_user_id=published_by_user_id,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def create_file(
        self,
        *,
        file_id: UUID,
        version_id: UUID,
        name: str,
        mime_type: str,
        size_bytes: int,
        storage_path: str,
        created_at: datetime,
    ) -> VersionFile:
        row = VersionFile(
            id=file_id,
            version_id=version_id,
            name=name,
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
            created_at=created_at,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def create_resource(
        self,
        *,
        version_id: UUID,
        title: str,
        url: str,
        resource_type,
        description: str | None,
        position: int,
    ) -> VersionResource:
        row = VersionResource(
            id=uuid4(),
            version_id=version_id,
            title=title,
            url=url,
            type=resource_type,
            description=description,
            position=position,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def list_files(self, *, version_id: UUID) -> list[VersionFile]:
        return (
            self.db.query(VersionFile)
            .filter(VersionFile.version_id == version_id)
            .order_by(VersionFile.created_at.asc())
            .all()
        )

    def get_file_for_version(
        self, *, version_id: UUID, file_id: UUID
    ) -> VersionFile | None:
        return (
            self.db.query(VersionFile)
            .filter(VersionFile.id == file_id, VersionFile.version_id == version_id)
            .one_or_none()
        )

    def list_resources(self, *, version_id: UUID) -> list[VersionResource]:
        return (
            self.db.query(VersionResource)
            .filter(VersionResource.version_id == version_id)
            .order_by(VersionResource.position.asc())
            .all()
        )
