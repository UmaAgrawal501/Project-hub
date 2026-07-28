from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.session import get_db
from app.schemas.share import PublicDownloadRequest
from app.services.share_service import ShareService
from app.storage.supabase_storage import SupabaseStorageClient

router = APIRouter(
    prefix="/public",
    tags=["public"],
)


def get_share_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ShareService:
    return ShareService(db, SupabaseStorageClient(settings))


@router.get("/{token}")
def get_public_portal(
    token: str,
    service: ShareService = Depends(get_share_service),
) -> dict:
    data = service.get_public_portal(token=token)
    return {"data": data.model_dump(mode="json")}


@router.get("/{token}/versions/{version_number}")
def get_public_portal_version(
    token: str,
    version_number: int,
    service: ShareService = Depends(get_share_service),
) -> dict:
    data = service.get_public_portal_version(token=token, version_number=version_number)
    return {"data": data.model_dump(mode="json")}


@router.post("/{token}/files/{file_id}/download-url")
def create_public_download_url(
    token: str,
    file_id: UUID,
    payload: PublicDownloadRequest = Body(default_factory=PublicDownloadRequest),
    service: ShareService = Depends(get_share_service),
) -> dict:
    data = service.create_public_download_url(
        token=token,
        file_id=file_id,
        version_number=payload.version_number,
    )
    return {"data": data.model_dump(mode="json")}
