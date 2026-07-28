from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Project, ProjectShare


class ShareRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_token(self, *, token: str) -> ProjectShare | None:
        return (
            self.db.query(ProjectShare)
            .filter(ProjectShare.token == token)
            .one_or_none()
        )

    def get_for_version(
        self, *, project_id: UUID, version_number: int
    ) -> ProjectShare | None:
        return (
            self.db.query(ProjectShare)
            .filter(
                ProjectShare.project_id == project_id,
                ProjectShare.version_number == version_number,
            )
            .one_or_none()
        )

    def get_latest_for_project(self, *, project_id: UUID) -> ProjectShare | None:
        return (
            self.db.query(ProjectShare)
            .filter(ProjectShare.project_id == project_id)
            .order_by(ProjectShare.version_number.desc())
            .first()
        )

    def list_for_project(self, *, project_id: UUID) -> list[ProjectShare]:
        return (
            self.db.query(ProjectShare)
            .filter(ProjectShare.project_id == project_id)
            .order_by(ProjectShare.version_number.desc())
            .all()
        )

    def create(
        self,
        *,
        project_id: UUID,
        token: str,
        version_number: int,
        is_enabled: bool = True,
    ) -> ProjectShare:
        share = ProjectShare(
            project_id=project_id,
            token=token,
            version_number=version_number,
            is_enabled=is_enabled,
        )
        self.db.add(share)
        self.db.flush()
        return share

    def save(self, share: ProjectShare) -> ProjectShare:
        self.db.add(share)
        self.db.flush()
        return share

    def disable_all_for_project(self, *, project_id: UUID) -> list[ProjectShare]:
        rows = self.list_for_project(project_id=project_id)
        for share in rows:
            if share.is_enabled:
                share.is_enabled = False
                self.db.add(share)
        self.db.flush()
        return rows

    def get_project(self, *, project_id: UUID) -> Project | None:
        return self.db.query(Project).filter(Project.id == project_id).one_or_none()
