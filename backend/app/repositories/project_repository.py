from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Project, ProjectShare, ProjectStatus


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_workspace(
        self,
        *,
        workspace_id: UUID,
        status: ProjectStatus,
        limit: int,
        offset: int,
    ) -> tuple[list[Project], int]:
        base = self.db.query(Project).filter(
            Project.workspace_id == workspace_id,
            Project.deleted_at.is_(None),
            Project.status == status,
        )
        total = base.with_entities(func.count(Project.id)).scalar() or 0
        items = (
            base.order_by(Project.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return items, int(total)

    def get_live_for_workspace(
        self, *, project_id: UUID, workspace_id: UUID
    ) -> Project | None:
        return (
            self.db.query(Project)
            .filter(
                Project.id == project_id,
                Project.workspace_id == workspace_id,
                Project.deleted_at.is_(None),
            )
            .one_or_none()
        )

    def create(
        self,
        *,
        workspace_id: UUID,
        name: str,
    ) -> Project:
        # Delivery overview lives on project_drafts (V2).
        project = Project(
            workspace_id=workspace_id,
            name=name,
            status=ProjectStatus.active,
            latest_version_number=None,
        )
        self.db.add(project)
        self.db.flush()
        return project

    def save(self, project: Project) -> Project:
        self.db.add(project)
        self.db.flush()
        return project

    def soft_delete(self, project: Project) -> None:
        project.deleted_at = datetime.now(timezone.utc)
        self.db.add(project)
        self.db.flush()

    def get_share(self, project_id: UUID) -> ProjectShare | None:
        """Return the share locked to the project's latest published version."""
        project = self.db.query(Project).filter(Project.id == project_id).one_or_none()
        if project is None or project.latest_version_number is None:
            return None
        return (
            self.db.query(ProjectShare)
            .filter(
                ProjectShare.project_id == project_id,
                ProjectShare.version_number == project.latest_version_number,
            )
            .one_or_none()
        )

    def disable_share_if_exists(self, project_id: UUID) -> None:
        rows = (
            self.db.query(ProjectShare)
            .filter(ProjectShare.project_id == project_id)
            .all()
        )
        for share in rows:
            if share.is_enabled:
                share.is_enabled = False
                self.db.add(share)
        if rows:
            self.db.flush()
