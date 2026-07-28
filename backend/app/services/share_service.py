from __future__ import annotations

import secrets
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Project, ProjectShare, Workspace
from app.repositories.project_repository import ProjectRepository
from app.repositories.share_repository import ShareRepository
from app.repositories.version_repository import VersionRepository
from app.schemas.draft import DownloadUrlOut
from app.schemas.projects import ProjectStatusValue, ShareOut
from app.schemas.resources import ResourceTypeValue
from app.schemas.share import (
    PublicFileOut,
    PublicPortalOut,
    PublicPortalProjectOut,
    PublicPortalVersionOut,
    PublicResourceOut,
    PublicVersionRefOut,
    ShareMutationOut,
    ShareStateOut,
)
from app.storage.supabase_storage import SupabaseStorageClient


def generate_share_token() -> str:
    return secrets.token_urlsafe(32)


class ShareService:
    def __init__(self, db: Session, storage: SupabaseStorageClient) -> None:
        self.db = db
        self.storage = storage
        self.shares = ShareRepository(db)
        self.projects = ProjectRepository(db)
        self.versions = VersionRepository(db)

    def list_shares(self, *, workspace: Workspace, project_id: UUID) -> list[ShareOut]:
        self._require_live_owned_project(workspace=workspace, project_id=project_id)
        return [
            self._to_share_out(row)
            for row in self.shares.list_for_project(project_id=project_id)
        ]

    def get_share_state(self, *, workspace: Workspace, project_id: UUID) -> ShareStateOut:
        project = self._require_live_owned_project(workspace=workspace, project_id=project_id)
        share = self._latest_share(project)
        if share is None:
            return ShareStateOut(enabled=False, share=None)
        return ShareStateOut(enabled=share.is_enabled, share=self._to_share_out(share))

    def enable_share(self, *, workspace: Workspace, project_id: UUID) -> ShareMutationOut:
        project = self._require_owned_project_for_share_mutation(
            workspace=workspace,
            project_id=project_id,
        )
        if project.latest_version_number is None:
            raise AppError(
                status_code=409,
                code="conflict",
                message="Publish a version before enabling share",
            )
        share = self.shares.get_for_version(
            project_id=project.id,
            version_number=int(project.latest_version_number),
        )
        if share is None:
            share = self.shares.create(
                project_id=project.id,
                token=generate_share_token(),
                version_number=int(project.latest_version_number),
                is_enabled=True,
            )
        else:
            share.is_enabled = True
            self.shares.save(share)
        self.db.commit()
        self.db.refresh(share)
        return ShareMutationOut(enabled=True, share=self._to_share_out(share))

    def disable_share(self, *, workspace: Workspace, project_id: UUID) -> ShareMutationOut:
        project = self._require_live_owned_project(workspace=workspace, project_id=project_id)
        rows = self.shares.list_for_project(project_id=project.id)
        if not rows:
            raise AppError(
                status_code=404,
                code="share_not_initialized",
                message="Sharing has not been enabled for this project",
            )
        self.shares.disable_all_for_project(project_id=project.id)
        self.db.commit()
        latest = self._latest_share(project)
        assert latest is not None
        self.db.refresh(latest)
        return ShareMutationOut(enabled=False, share=self._to_share_out(latest))

    def regenerate_share(self, *, workspace: Workspace, project_id: UUID) -> ShareMutationOut:
        project = self._require_live_owned_project(workspace=workspace, project_id=project_id)
        share = self._latest_share(project)
        if share is None:
            raise AppError(
                status_code=404,
                code="share_not_initialized",
                message="Sharing has not been enabled for this project",
            )
        share.token = generate_share_token()
        share.is_enabled = True
        self.shares.save(share)
        self.db.commit()
        self.db.refresh(share)
        return ShareMutationOut(enabled=True, share=self._to_share_out(share))

    def get_public_portal(self, *, token: str) -> PublicPortalOut:
        project, share = self._resolve_public_share(token=token)
        return self._build_portal(
            project=project,
            version_number=int(share.version_number),
        )

    def get_public_portal_version(self, *, token: str, version_number: int) -> PublicPortalOut:
        project, share = self._resolve_public_share(token=token)
        if int(version_number) != int(share.version_number):
            raise AppError(
                status_code=404,
                code="share_unavailable",
                message="This link is no longer active",
            )
        return self._build_portal(project=project, version_number=int(share.version_number))

    def create_public_download_url(
        self,
        *,
        token: str,
        file_id: UUID,
        version_number: int | None = None,
    ) -> DownloadUrlOut:
        project, share = self._resolve_public_share(token=token)
        locked = int(share.version_number)
        if version_number is not None and int(version_number) != locked:
            raise AppError(
                status_code=404,
                code="share_unavailable",
                message="This link is no longer active",
            )
        version_number = locked

        version = self.versions.get_by_number(
            project_id=project.id, version_number=version_number
        )
        if version is None:
            raise AppError(
                status_code=404,
                code="share_unavailable",
                message="This link is no longer active",
            )

        row = self.versions.get_file_for_version(version_id=version.id, file_id=file_id)
        if row is None:
            raise AppError(
                status_code=404,
                code="share_unavailable",
                message="This link is no longer active",
            )

        signed = self.storage.create_signed_download_url(storage_path=row.storage_path)
        return DownloadUrlOut(
            download_url=signed.download_url,
            expires_at=signed.expires_at,
            name=row.name,
        )

    def _build_portal(self, *, project: Project, version_number: int) -> PublicPortalOut:
        version = self.versions.get_by_number(
            project_id=project.id, version_number=version_number
        )
        if version is None:
            raise AppError(
                status_code=404,
                code="share_unavailable",
                message="This link is no longer active",
            )

        files = [
            PublicFileOut(
                id=row.id,
                name=row.name,
                mime_type=row.mime_type,
                size_bytes=row.size_bytes,
                created_at=row.created_at,
            )
            for row in self.versions.list_files(version_id=version.id)
        ]
        resources = [
            PublicResourceOut(
                id=row.id,
                title=row.title,
                url=row.url,
                type=ResourceTypeValue(row.type.value),
                description=row.description,
                position=row.position,
            )
            for row in self.versions.list_resources(version_id=version.id)
        ]
        # Token is version-locked: expose only that version (no switcher).
        versions_available = [
            PublicVersionRefOut(
                version_number=version.version_number,
                published_at=version.published_at,
            )
        ]

        return PublicPortalOut(
            project=PublicPortalProjectOut(
                name=version.name,
                status=ProjectStatusValue(project.status.value),
            ),
            version=PublicPortalVersionOut(
                version_number=version.version_number,
                name=version.name,
                release_notes=version.release_notes,
                overview=version.overview,
                published_at=version.published_at,
            ),
            resources=resources,
            files=files,
            versions_available=versions_available,
        )

    def _resolve_public_share(self, *, token: str) -> tuple[Project, ProjectShare]:
        share = self.shares.get_by_token(token=token)
        if share is None or not share.is_enabled:
            raise AppError(
                status_code=404,
                code="share_unavailable",
                message="This link is no longer active",
            )
        project = self.shares.get_project(project_id=share.project_id)
        if project is None or project.deleted_at is not None:
            raise AppError(
                status_code=404,
                code="share_unavailable",
                message="This link is no longer active",
            )
        if (
            self.versions.get_by_number(
                project_id=project.id, version_number=int(share.version_number)
            )
            is None
        ):
            raise AppError(
                status_code=404,
                code="share_unavailable",
                message="This link is no longer active",
            )
        return project, share

    def _latest_share(self, project: Project) -> ProjectShare | None:
        if project.latest_version_number is None:
            return None
        return self.shares.get_for_version(
            project_id=project.id,
            version_number=int(project.latest_version_number),
        )

    def _require_live_owned_project(self, *, workspace: Workspace, project_id: UUID) -> Project:
        project = self.projects.get_live_for_workspace(
            project_id=project_id,
            workspace_id=workspace.id,
        )
        if project is None:
            raise AppError(status_code=404, code="not_found", message="Project not found")
        return project

    def _require_owned_project_for_share_mutation(
        self, *, workspace: Workspace, project_id: UUID
    ) -> Project:
        project = (
            self.db.query(Project)
            .filter(Project.id == project_id, Project.workspace_id == workspace.id)
            .one_or_none()
        )
        if project is None:
            raise AppError(status_code=404, code="not_found", message="Project not found")
        if project.deleted_at is not None:
            raise AppError(
                status_code=409,
                code="project_deleted",
                message="This project has been deleted",
            )
        return project

    def _to_share_out(self, share: ProjectShare) -> ShareOut:
        return ShareOut(
            id=share.id,
            project_id=share.project_id,
            version_number=share.version_number,
            token=share.token,
            is_enabled=share.is_enabled,
            public_path=f"/p/{share.token}",
            created_at=share.created_at,
            updated_at=share.updated_at,
        )
