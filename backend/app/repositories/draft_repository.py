from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import DraftFile, DraftResource, ProjectDraft, ResourceType


class DraftRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, *, project_id: UUID) -> ProjectDraft | None:
        return (
            self.db.query(ProjectDraft)
            .filter(ProjectDraft.project_id == project_id)
            .one_or_none()
        )

    def create(self, *, project_id: UUID, overview: str | None = None) -> ProjectDraft:
        draft = ProjectDraft(
            project_id=project_id,
            overview=overview,
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(draft)
        self.db.flush()
        return draft

    def get_or_create(self, *, project_id: UUID) -> ProjectDraft:
        draft = self.get(project_id=project_id)
        if draft is not None:
            return draft
        return self.create(project_id=project_id, overview=None)

    def save(self, draft: ProjectDraft) -> ProjectDraft:
        draft.updated_at = datetime.now(timezone.utc)
        self.db.add(draft)
        self.db.flush()
        return draft

    def touch(self, *, project_id: UUID) -> ProjectDraft:
        draft = self.get_or_create(project_id=project_id)
        return self.save(draft)


class DraftFileRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_project(self, *, project_id: UUID) -> list[DraftFile]:
        return (
            self.db.query(DraftFile)
            .filter(DraftFile.project_id == project_id)
            .order_by(DraftFile.created_at.desc())
            .all()
        )

    def count_for_project(self, *, project_id: UUID) -> int:
        return int(
            self.db.query(func.count(DraftFile.id))
            .filter(DraftFile.project_id == project_id)
            .scalar()
            or 0
        )

    def get_for_project(self, *, project_id: UUID, file_id: UUID) -> DraftFile | None:
        return (
            self.db.query(DraftFile)
            .filter(DraftFile.id == file_id, DraftFile.project_id == project_id)
            .one_or_none()
        )

    def get_by_storage_path(self, *, storage_path: str) -> DraftFile | None:
        return (
            self.db.query(DraftFile)
            .filter(DraftFile.storage_path == storage_path)
            .one_or_none()
        )

    def create(
        self,
        *,
        file_id: UUID,
        project_id: UUID,
        name: str,
        storage_path: str,
        mime_type: str,
        size_bytes: int,
        uploaded_by_user_id: UUID,
    ) -> DraftFile:
        row = DraftFile(
            id=file_id,
            project_id=project_id,
            name=name,
            storage_path=storage_path,
            mime_type=mime_type,
            size_bytes=size_bytes,
            uploaded_by_user_id=uploaded_by_user_id,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def delete(self, row: DraftFile) -> None:
        self.db.delete(row)
        self.db.flush()


class DraftResourceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_project(self, *, project_id: UUID) -> list[DraftResource]:
        return (
            self.db.query(DraftResource)
            .filter(DraftResource.project_id == project_id)
            .order_by(DraftResource.position.asc(), DraftResource.created_at.asc())
            .all()
        )

    def count_for_project(self, *, project_id: UUID) -> int:
        return int(
            self.db.query(func.count(DraftResource.id))
            .filter(DraftResource.project_id == project_id)
            .scalar()
            or 0
        )

    def get_for_project(
        self, *, project_id: UUID, resource_id: UUID
    ) -> DraftResource | None:
        return (
            self.db.query(DraftResource)
            .filter(
                DraftResource.id == resource_id,
                DraftResource.project_id == project_id,
            )
            .one_or_none()
        )

    def next_position(self, *, project_id: UUID) -> int:
        current_max = (
            self.db.query(func.max(DraftResource.position))
            .filter(DraftResource.project_id == project_id)
            .scalar()
        )
        if current_max is None:
            return 0
        return int(current_max) + 1

    def create(
        self,
        *,
        project_id: UUID,
        title: str,
        url: str,
        resource_type: ResourceType,
        description: str | None,
        position: int,
    ) -> DraftResource:
        resource = DraftResource(
            project_id=project_id,
            title=title,
            url=url,
            type=resource_type,
            description=description,
            position=position,
        )
        self.db.add(resource)
        self.db.flush()
        return resource

    def save(self, resource: DraftResource) -> DraftResource:
        self.db.add(resource)
        self.db.flush()
        return resource

    def delete(self, resource: DraftResource) -> None:
        self.db.delete(resource)
        self.db.flush()
