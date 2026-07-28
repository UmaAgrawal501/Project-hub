from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Project, Workspace
from app.repositories.project_repository import ProjectRepository


def require_owned_project(
    db: Session,
    *,
    workspace: Workspace,
    project_id: UUID,
) -> Project:
    project = ProjectRepository(db).get_live_for_workspace(
        project_id=project_id,
        workspace_id=workspace.id,
    )
    if project is None:
        raise AppError(status_code=404, code="not_found", message="Project not found")
    return project
