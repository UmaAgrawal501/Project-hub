from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import CurrentUserContext, get_current_user
from app.database.session import get_db
from app.schemas.projects import (
    ProjectCreateRequest,
    ProjectStatusValue,
    ProjectUpdateRequest,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    return ProjectService(db)


@router.get("")
def list_projects(
    status: ProjectStatusValue = Query(default=ProjectStatusValue.active),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current: CurrentUserContext = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> dict:
    data, meta = service.list_projects(
        workspace=current.workspace,
        status=status,
        limit=limit,
        offset=offset,
    )
    return {
        "data": [item.model_dump(mode="json") for item in data],
        "meta": meta.model_dump(mode="json"),
    }


@router.post("", status_code=201)
def create_project(
    payload: ProjectCreateRequest,
    current: CurrentUserContext = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> dict:
    data = service.create_project(workspace=current.workspace, payload=payload)
    return {"data": data.model_dump(mode="json")}


@router.get("/{project_id}")
def get_project(
    project_id: UUID,
    current: CurrentUserContext = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> dict:
    data = service.get_project(workspace=current.workspace, project_id=project_id)
    return {"data": data.model_dump(mode="json")}


@router.patch("/{project_id}")
def update_project(
    project_id: UUID,
    payload: ProjectUpdateRequest,
    current: CurrentUserContext = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> dict:
    data = service.update_project(
        workspace=current.workspace,
        project_id=project_id,
        payload=payload,
    )
    return {"data": data.model_dump(mode="json")}


@router.delete("/{project_id}")
def delete_project(
    project_id: UUID,
    current: CurrentUserContext = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> dict:
    data = service.delete_project(workspace=current.workspace, project_id=project_id)
    return {"data": data}
