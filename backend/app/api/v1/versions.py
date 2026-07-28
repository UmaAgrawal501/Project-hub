from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.deps import CurrentUserContext, get_current_user
from app.database.session import get_db
from app.schemas.versions import PublishRequest
from app.services.publish_service import PublishService
from app.storage.supabase_storage import SupabaseStorageClient

router = APIRouter(prefix="/projects/{project_id}", tags=["versions"])


def get_publish_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PublishService:
    return PublishService(db, settings, SupabaseStorageClient(settings))


@router.post("/publish", status_code=201)
def publish_project(
    project_id: UUID,
    payload: PublishRequest,
    current: CurrentUserContext = Depends(get_current_user),
    service: PublishService = Depends(get_publish_service),
) -> dict:
    data = service.publish(
        workspace=current.workspace,
        user=current.user,
        project_id=project_id,
        payload=payload,
    )
    return {"data": data.model_dump(mode="json")}


@router.get("/versions")
def list_versions(
    project_id: UUID,
    current: CurrentUserContext = Depends(get_current_user),
    service: PublishService = Depends(get_publish_service),
) -> dict:
    data = service.list_versions(workspace=current.workspace, project_id=project_id)
    return {"data": [item.model_dump(mode="json") for item in data]}


@router.get("/versions/{version_number}")
def get_version(
    project_id: UUID,
    version_number: int,
    current: CurrentUserContext = Depends(get_current_user),
    service: PublishService = Depends(get_publish_service),
) -> dict:
    data = service.get_version(
        workspace=current.workspace,
        project_id=project_id,
        version_number=version_number,
    )
    return {"data": data.model_dump(mode="json")}


@router.post("/versions/{version_number}/files/{file_id}/download-url")
def create_version_download_url(
    project_id: UUID,
    version_number: int,
    file_id: UUID,
    current: CurrentUserContext = Depends(get_current_user),
    service: PublishService = Depends(get_publish_service),
) -> dict:
    # API Contract §7.4 specifies POST (not GET).
    data = service.create_version_download_url(
        workspace=current.workspace,
        project_id=project_id,
        version_number=version_number,
        file_id=file_id,
    )
    return {"data": data.model_dump(mode="json")}
