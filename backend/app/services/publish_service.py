from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.models import Project, User, Workspace
from app.repositories.draft_repository import (
    DraftFileRepository,
    DraftRepository,
    DraftResourceRepository,
)
from app.repositories.project_repository import ProjectRepository
from app.repositories.share_repository import ShareRepository
from app.repositories.version_repository import VersionRepository
from app.schemas.draft import DownloadUrlOut
from app.schemas.projects import ShareOut
from app.schemas.resources import ResourceTypeValue
from app.schemas.versions import (
    PublishRequest,
    PublishResultOut,
    VersionDetailOut,
    VersionFileOut,
    VersionOut,
    VersionResourceOut,
    VersionSummaryOut,
)
from app.services.share_service import generate_share_token
from app.storage.supabase_storage import SupabaseStorageClient
from app.utils.filenames import safe_filename


class PublishService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        storage: SupabaseStorageClient,
    ) -> None:
        self.db = db
        self.settings = settings
        self.storage = storage
        self.projects = ProjectRepository(db)
        self.drafts = DraftRepository(db)
        self.draft_files = DraftFileRepository(db)
        self.draft_resources = DraftResourceRepository(db)
        self.versions = VersionRepository(db)
        self.shares = ShareRepository(db)

    def publish(
        self,
        *,
        workspace: Workspace,
        user: User,
        project_id: UUID,
        payload: PublishRequest,
    ) -> PublishResultOut:
        project = self._require_project_for_publish(
            workspace_id=workspace.id, project_id=project_id
        )

        # Lock project row to serialize concurrent publishes.
        locked = (
            self.db.query(Project)
            .filter(Project.id == project.id)
            .with_for_update()
            .one()
        )

        draft = self.drafts.get_or_create(project_id=locked.id)
        draft_files = self.draft_files.list_for_project(project_id=locked.id)
        draft_resources = self.draft_resources.list_for_project(project_id=locked.id)

        overview = draft.overview
        has_overview = bool(overview and overview.strip())
        if not has_overview and not draft_files and not draft_resources:
            raise AppError(
                status_code=409,
                code="nothing_to_publish",
                message="Draft has nothing to publish",
            )

        max_n = self.versions.max_version_number(project_id=locked.id)
        next_n = int(max_n or 0) + 1
        published_at = datetime.now(timezone.utc)

        # Copy storage first; roll back objects if DB commit fails.
        copied_paths: list[str] = []
        planned_files: list[tuple[object, UUID, str]] = []
        try:
            for draft_file in draft_files:
                version_file_id = uuid4()
                dest = (
                    f"{workspace.id}/{locked.id}/versions/{next_n}/"
                    f"{version_file_id}/{safe_filename(draft_file.name)}"
                )
                self.storage.copy_object(
                    source_path=draft_file.storage_path,
                    dest_path=dest,
                )
                copied_paths.append(dest)
                planned_files.append((draft_file, version_file_id, dest))

            version = self.versions.create_version(
                project_id=locked.id,
                version_number=next_n,
                name=locked.name,
                release_notes=payload.release_notes,
                overview=overview if has_overview else None,
                published_at=published_at,
                published_by_user_id=user.id,
            )

            version_file_rows = []
            for draft_file, version_file_id, dest in planned_files:
                row = self.versions.create_file(
                    file_id=version_file_id,
                    version_id=version.id,
                    name=draft_file.name,
                    mime_type=draft_file.mime_type,
                    size_bytes=draft_file.size_bytes,
                    storage_path=dest,
                    created_at=published_at,
                )
                version_file_rows.append(row)

            version_resource_rows = []
            for resource in draft_resources:
                version_resource_rows.append(
                    self.versions.create_resource(
                        version_id=version.id,
                        title=resource.title,
                        url=resource.url,
                        resource_type=resource.type,
                        description=resource.description,
                        position=resource.position,
                    )
                )

            locked.latest_version_number = next_n
            self.projects.save(locked)

            share = self.shares.create(
                project_id=locked.id,
                token=generate_share_token(),
                version_number=next_n,
                is_enabled=True,
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            self._cleanup_copied(copied_paths)
            raise AppError(
                status_code=409,
                code="conflict",
                message="Another publish completed concurrently; retry",
            ) from exc
        except AppError:
            self.db.rollback()
            self._cleanup_copied(copied_paths)
            raise
        except Exception as exc:
            self.db.rollback()
            self._cleanup_copied(copied_paths)
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Unable to publish version",
            ) from exc

        self.db.refresh(version)
        self.db.refresh(share)
        for row in version_file_rows:
            self.db.refresh(row)
        for row in version_resource_rows:
            self.db.refresh(row)

        return PublishResultOut(
            version=self._to_version_out(version),
            files=[VersionFileOut.model_validate(f) for f in version_file_rows],
            resources=[self._to_resource_out(r) for r in version_resource_rows],
            share=ShareOut(
                id=share.id,
                project_id=share.project_id,
                version_number=share.version_number,
                token=share.token,
                is_enabled=share.is_enabled,
                public_path=f"/p/{share.token}",
                created_at=share.created_at,
                updated_at=share.updated_at,
            ),
        )

    def list_versions(
        self, *, workspace: Workspace, project_id: UUID
    ) -> list[VersionSummaryOut]:
        project = self._require_live_project(
            workspace_id=workspace.id, project_id=project_id
        )
        rows = self.versions.list_for_project(project_id=project.id)
        return [
            VersionSummaryOut(
                id=row.id,
                project_id=row.project_id,
                version_number=row.version_number,
                name=row.name,
                release_notes=row.release_notes,
                overview=row.overview,
                published_at=row.published_at,
            )
            for row in rows
        ]

    def get_version(
        self,
        *,
        workspace: Workspace,
        project_id: UUID,
        version_number: int,
    ) -> VersionDetailOut:
        project = self._require_live_project(
            workspace_id=workspace.id, project_id=project_id
        )
        version = self.versions.get_by_number(
            project_id=project.id, version_number=version_number
        )
        if version is None:
            raise AppError(status_code=404, code="not_found", message="Version not found")
        files = self.versions.list_files(version_id=version.id)
        resources = self.versions.list_resources(version_id=version.id)
        return VersionDetailOut(
            version=self._to_version_out(version),
            files=[VersionFileOut.model_validate(f) for f in files],
            resources=[self._to_resource_out(r) for r in resources],
        )

    def create_version_download_url(
        self,
        *,
        workspace: Workspace,
        project_id: UUID,
        version_number: int,
        file_id: UUID,
    ) -> DownloadUrlOut:
        project = self._require_live_project(
            workspace_id=workspace.id, project_id=project_id
        )
        version = self.versions.get_by_number(
            project_id=project.id, version_number=version_number
        )
        if version is None:
            raise AppError(status_code=404, code="not_found", message="Version not found")
        row = self.versions.get_file_for_version(version_id=version.id, file_id=file_id)
        if row is None:
            raise AppError(status_code=404, code="not_found", message="File not found")
        signed = self.storage.create_signed_download_url(storage_path=row.storage_path)
        return DownloadUrlOut(
            download_url=signed.download_url,
            expires_at=signed.expires_at,
            name=row.name,
        )

    def _require_live_project(self, *, workspace_id: UUID, project_id: UUID) -> Project:
        project = self.projects.get_live_for_workspace(
            project_id=project_id, workspace_id=workspace_id
        )
        if project is None:
            raise AppError(status_code=404, code="not_found", message="Project not found")
        return project

    def _require_project_for_publish(
        self, *, workspace_id: UUID, project_id: UUID
    ) -> Project:
        project = (
            self.db.query(Project)
            .filter(Project.id == project_id, Project.workspace_id == workspace_id)
            .one_or_none()
        )
        if project is None:
            raise AppError(status_code=404, code="not_found", message="Project not found")
        if project.deleted_at is not None:
            raise AppError(
                status_code=409,
                code="project_deleted",
                message="Project has been deleted",
            )
        return project

    def _cleanup_copied(self, paths: list[str]) -> None:
        for path in paths:
            try:
                self.storage.delete_object(storage_path=path)
            except AppError:
                pass

    def _to_version_out(self, version) -> VersionOut:
        return VersionOut(
            id=version.id,
            project_id=version.project_id,
            version_number=version.version_number,
            name=version.name,
            release_notes=version.release_notes,
            overview=version.overview,
            published_at=version.published_at,
            published_by_user_id=version.published_by_user_id,
        )

    def _to_resource_out(self, row) -> VersionResourceOut:
        return VersionResourceOut(
            id=row.id,
            title=row.title,
            url=row.url,
            type=ResourceTypeValue(row.type.value),
            description=row.description,
            position=row.position,
        )
