from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.deps import CurrentUserContext, get_current_user
from app.database.session import get_db
from app.schemas.draft import (
    DraftConfirmUploadRequest,
    DraftResourceCreateRequest,
    DraftResourceUpdateRequest,
    DraftUpdateRequest,
    DraftUploadUrlRequest,
)
from app.services.draft_service import DraftService
from app.storage.supabase_storage import SupabaseStorageClient

router = APIRouter(prefix="/projects/{project_id}", tags=["draft"])


def get_draft_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DraftService:
    return DraftService(db, settings, SupabaseStorageClient(settings))


@router.get("/draft")
def get_draft(
    project_id: UUID,
    current: CurrentUserContext = Depends(get_current_user),
    service: DraftService = Depends(get_draft_service),
) -> dict:
    data = service.get_draft(workspace=current.workspace, project_id=project_id)
    return {"data": data.model_dump(mode="json")}


@router.patch("/draft")
def update_draft(
    project_id: UUID,
    payload: DraftUpdateRequest,
    current: CurrentUserContext = Depends(get_current_user),
    service: DraftService = Depends(get_draft_service),
) -> dict:
    data = service.update_draft(
        workspace=current.workspace,
        project_id=project_id,
        payload=payload,
    )
    return {"data": data.model_dump(mode="json")}


@router.get("/draft/files")
def list_draft_files(
    project_id: UUID,
    current: CurrentUserContext = Depends(get_current_user),
    service: DraftService = Depends(get_draft_service),
) -> dict:
    data = service.list_files(workspace=current.workspace, project_id=project_id)
    return {"data": [item.model_dump(mode="json") for item in data]}


@router.post("/draft/files/upload-url")
def create_draft_upload_url(
    project_id: UUID,
    payload: DraftUploadUrlRequest,
    current: CurrentUserContext = Depends(get_current_user),
    service: DraftService = Depends(get_draft_service),
) -> dict:
    data = service.create_upload_url(
        workspace=current.workspace,
        project_id=project_id,
        payload=payload,
    )
    return {"data": data.model_dump(mode="json")}


@router.post("/draft/files/confirm", status_code=201)
def confirm_draft_upload(
    project_id: UUID,
    payload: DraftConfirmUploadRequest,
    current: CurrentUserContext = Depends(get_current_user),
    service: DraftService = Depends(get_draft_service),
) -> dict:
    data = service.confirm_upload(
        workspace=current.workspace,
        user=current.user,
        project_id=project_id,
        payload=payload,
    )
    return {"data": data.model_dump(mode="json")}


@router.post("/draft/files/{file_id}/download-url")
def create_draft_download_url(
    project_id: UUID,
    file_id: UUID,
    current: CurrentUserContext = Depends(get_current_user),
    service: DraftService = Depends(get_draft_service),
) -> dict:
    data = service.create_download_url(
        workspace=current.workspace,
        project_id=project_id,
        file_id=file_id,
    )
    return {"data": data.model_dump(mode="json")}


@router.delete("/draft/files/{file_id}")
def delete_draft_file(
    project_id: UUID,
    file_id: UUID,
    current: CurrentUserContext = Depends(get_current_user),
    service: DraftService = Depends(get_draft_service),
) -> dict:
    data = service.delete_file(
        workspace=current.workspace,
        project_id=project_id,
        file_id=file_id,
    )
    return {"data": data}


@router.get("/draft/resources")
def list_draft_resources(
    project_id: UUID,
    current: CurrentUserContext = Depends(get_current_user),
    service: DraftService = Depends(get_draft_service),
) -> dict:
    data = service.list_resources(workspace=current.workspace, project_id=project_id)
    return {"data": [item.model_dump(mode="json") for item in data]}


@router.post("/draft/resources", status_code=201)
def create_draft_resource(
    project_id: UUID,
    payload: DraftResourceCreateRequest,
    current: CurrentUserContext = Depends(get_current_user),
    service: DraftService = Depends(get_draft_service),
) -> dict:
    data = service.create_resource(
        workspace=current.workspace,
        project_id=project_id,
        payload=payload,
    )
    return {"data": data.model_dump(mode="json")}


@router.patch("/draft/resources/{resource_id}")
def update_draft_resource(
    project_id: UUID,
    resource_id: UUID,
    payload: DraftResourceUpdateRequest,
    current: CurrentUserContext = Depends(get_current_user),
    service: DraftService = Depends(get_draft_service),
) -> dict:
    data = service.update_resource(
        workspace=current.workspace,
        project_id=project_id,
        resource_id=resource_id,
        payload=payload,
    )
    return {"data": data.model_dump(mode="json")}


@router.delete("/draft/resources/{resource_id}")
def delete_draft_resource(
    project_id: UUID,
    resource_id: UUID,
    current: CurrentUserContext = Depends(get_current_user),
    service: DraftService = Depends(get_draft_service),
) -> dict:
    data = service.delete_resource(
        workspace=current.workspace,
        project_id=project_id,
        resource_id=resource_id,
    )
    return {"data": data}
