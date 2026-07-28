from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.deps import CurrentUserContext, get_current_user
from app.database.session import get_db
from app.services.share_service import ShareService
from app.storage.supabase_storage import SupabaseStorageClient

router = APIRouter(tags=["share"])


def get_share_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ShareService:
    return ShareService(db, SupabaseStorageClient(settings))


@router.get("/projects/{project_id}/shares")
def list_shares(
    project_id: UUID,
    current: CurrentUserContext = Depends(get_current_user),
    service: ShareService = Depends(get_share_service),
) -> dict:
    data = service.list_shares(workspace=current.workspace, project_id=project_id)
    return {"data": [item.model_dump(mode="json") for item in data]}


@router.get("/projects/{project_id}/share")
def get_share_state(
    project_id: UUID,
    current: CurrentUserContext = Depends(get_current_user),
    service: ShareService = Depends(get_share_service),
) -> dict:
    data = service.get_share_state(workspace=current.workspace, project_id=project_id)
    return {"data": data.model_dump(mode="json")}


@router.post("/projects/{project_id}/share/enable")
def enable_share(
    project_id: UUID,
    current: CurrentUserContext = Depends(get_current_user),
    service: ShareService = Depends(get_share_service),
) -> dict:
    data = service.enable_share(workspace=current.workspace, project_id=project_id)
    return {"data": data.model_dump(mode="json")}


@router.post("/projects/{project_id}/share/disable")
def disable_share(
    project_id: UUID,
    current: CurrentUserContext = Depends(get_current_user),
    service: ShareService = Depends(get_share_service),
) -> dict:
    data = service.disable_share(workspace=current.workspace, project_id=project_id)
    return {"data": data.model_dump(mode="json")}


@router.post("/projects/{project_id}/share/regenerate")
def regenerate_share(
    project_id: UUID,
    current: CurrentUserContext = Depends(get_current_user),
    service: ShareService = Depends(get_share_service),
) -> dict:
    data = service.regenerate_share(workspace=current.workspace, project_id=project_id)
    return {"data": data.model_dump(mode="json")}
