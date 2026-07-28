from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Project, ProjectShare, ProjectStatus, Workspace
from app.repositories.draft_repository import (
    DraftFileRepository,
    DraftRepository,
    DraftResourceRepository,
)
from app.repositories.project_repository import ProjectRepository
from app.schemas.draft import DraftSummaryOut
from app.schemas.projects import (
    ProjectCreateRequest,
    ProjectDetailOut,
    ProjectListMeta,
    ProjectStatusValue,
    ProjectSummaryOut,
    ProjectUpdateRequest,
    ShareOut,
)
from app.services.dirty import has_unpublished_changes


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.drafts = DraftRepository(db)
        self.draft_files = DraftFileRepository(db)
        self.draft_resources = DraftResourceRepository(db)

    def list_projects(
        self,
        *,
        workspace: Workspace,
        status: ProjectStatusValue = ProjectStatusValue.active,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ProjectSummaryOut], ProjectListMeta]:
        if limit < 1 or limit > 100:
            raise AppError(
                status_code=400,
                code="validation_error",
                message="Request failed validation",
                details=[{"field": "limit", "message": "Must be between 1 and 100", "code": "range"}],
            )
        if offset < 0:
            raise AppError(
                status_code=400,
                code="validation_error",
                message="Request failed validation",
                details=[{"field": "offset", "message": "Must be >= 0", "code": "range"}],
            )

        items, total = self.projects.list_for_workspace(
            workspace_id=workspace.id,
            status=ProjectStatus(status.value),
            limit=limit,
            offset=offset,
        )
        data = [self._to_summary(item) for item in items]
        meta = ProjectListMeta(limit=limit, offset=offset, total=total)
        return data, meta

    def create_project(
        self, *, workspace: Workspace, payload: ProjectCreateRequest
    ) -> ProjectDetailOut:
        project = self.projects.create(
            workspace_id=workspace.id,
            name=payload.name,
        )
        self.drafts.create(project_id=project.id, overview=payload.overview)
        self.db.commit()
        self.db.refresh(project)
        return self._to_detail(project, share=None)

    def get_project(self, *, workspace: Workspace, project_id: UUID) -> ProjectDetailOut:
        project = self._require_project(workspace_id=workspace.id, project_id=project_id)
        share = self.projects.get_share(project.id)
        return self._to_detail(project, share=share)

    def update_project(
        self,
        *,
        workspace: Workspace,
        project_id: UUID,
        payload: ProjectUpdateRequest,
    ) -> ProjectDetailOut:
        if payload.name is None and payload.status is None:
            raise AppError(
                status_code=400,
                code="validation_error",
                message="Request failed validation",
                details=[
                    {
                        "field": "body",
                        "message": "At least one field is required",
                        "code": "required",
                    }
                ],
            )

        project = self._require_project(workspace_id=workspace.id, project_id=project_id)
        if payload.name is not None:
            project.name = payload.name
        if payload.status is not None:
            project.status = ProjectStatus(payload.status.value)

        self.projects.save(project)
        self.db.commit()
        self.db.refresh(project)
        share = self.projects.get_share(project.id)
        return self._to_detail(project, share=share)

    def delete_project(self, *, workspace: Workspace, project_id: UUID) -> dict:
        project = self._require_project(workspace_id=workspace.id, project_id=project_id)
        self.projects.disable_share_if_exists(project.id)
        self.projects.soft_delete(project)
        self.db.commit()
        return {"ok": True}

    def _require_project(self, *, workspace_id: UUID, project_id: UUID) -> Project:
        project = self.projects.get_live_for_workspace(
            project_id=project_id, workspace_id=workspace_id
        )
        if project is None:
            raise AppError(status_code=404, code="not_found", message="Project not found")
        return project

    def _to_summary(self, project: Project) -> ProjectSummaryOut:
        return ProjectSummaryOut(
            id=project.id,
            workspace_id=project.workspace_id,
            name=project.name,
            status=ProjectStatusValue(project.status.value),
            created_at=project.created_at,
            updated_at=project.updated_at,
            latest_version_number=project.latest_version_number,
            has_unpublished_changes=has_unpublished_changes(project, self.db),
        )

    def _to_detail(self, project: Project, *, share: ProjectShare | None) -> ProjectDetailOut:
        draft = self.drafts.get(project_id=project.id)
        if draft is None:
            draft = self.drafts.create(project_id=project.id, overview=None)
            self.db.commit()
            self.db.refresh(draft)

        summary = self._to_summary(project)
        share_out: ShareOut | None = None
        if share is not None:
            share_out = ShareOut(
                id=share.id,
                project_id=share.project_id,
                version_number=share.version_number,
                token=share.token,
                is_enabled=share.is_enabled,
                public_path=f"/p/{share.token}",
                created_at=share.created_at,
                updated_at=share.updated_at,
            )
        return ProjectDetailOut(
            **summary.model_dump(),
            draft=DraftSummaryOut(
                overview=draft.overview,
                updated_at=draft.updated_at,
                has_unpublished_changes=summary.has_unpublished_changes,
                file_count=self.draft_files.count_for_project(project_id=project.id),
                resource_count=self.draft_resources.count_for_project(project_id=project.id),
            ),
            share=share_out,
        )
