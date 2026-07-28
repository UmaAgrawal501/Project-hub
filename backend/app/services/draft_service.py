from __future__ import annotations

from uuid import UUID, uuid4

import jwt
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.core.limits import (
    DRAFT_FILE_MAX_BYTES,
    DRAFT_FILE_MIME_ALLOWLIST,
    DRAFT_FILE_NAME_MAX,
    DRAFT_FILES_MAX_PER_PROJECT,
)
from app.models import ResourceType, User, Workspace
from app.repositories.draft_repository import (
    DraftFileRepository,
    DraftRepository,
    DraftResourceRepository,
)
from app.schemas.draft import (
    DraftConfirmUploadRequest,
    DraftFileOut,
    DraftOut,
    DraftResourceCreateRequest,
    DraftResourceOut,
    DraftResourceUpdateRequest,
    DraftUpdateRequest,
    DraftUploadUrlOut,
    DraftUploadUrlRequest,
    DownloadUrlOut,
)
from app.services.dirty import has_unpublished_changes
from app.services.ownership import require_owned_project
from app.storage.supabase_storage import SupabaseStorageClient
from app.utils.filenames import safe_filename


class DraftService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        storage: SupabaseStorageClient,
    ) -> None:
        self.db = db
        self.settings = settings
        self.storage = storage
        self.drafts = DraftRepository(db)
        self.files = DraftFileRepository(db)
        self.resources = DraftResourceRepository(db)

    def get_draft(self, *, workspace: Workspace, project_id: UUID) -> DraftOut:
        project = require_owned_project(self.db, workspace=workspace, project_id=project_id)
        draft = self.drafts.get_or_create(project_id=project.id)
        self.db.commit()
        self.db.refresh(draft)
        return DraftOut(
            overview=draft.overview,
            updated_at=draft.updated_at,
            has_unpublished_changes=has_unpublished_changes(project, self.db),
        )

    def update_draft(
        self,
        *,
        workspace: Workspace,
        project_id: UUID,
        payload: DraftUpdateRequest,
    ) -> DraftOut:
        if "overview" not in payload.model_fields_set:
            raise AppError(
                status_code=400,
                code="validation_error",
                message="Request failed validation",
                details=[
                    {
                        "field": "overview",
                        "message": "overview is required",
                        "code": "required",
                    }
                ],
            )
        project = require_owned_project(self.db, workspace=workspace, project_id=project_id)
        draft = self.drafts.get_or_create(project_id=project.id)
        draft.overview = payload.overview
        self.drafts.save(draft)
        self.db.commit()
        self.db.refresh(draft)
        self.db.refresh(project)
        return DraftOut(
            overview=draft.overview,
            updated_at=draft.updated_at,
            has_unpublished_changes=has_unpublished_changes(project, self.db),
        )

    def list_files(self, *, workspace: Workspace, project_id: UUID) -> list[DraftFileOut]:
        project = require_owned_project(self.db, workspace=workspace, project_id=project_id)
        rows = self.files.list_for_project(project_id=project.id)
        return [DraftFileOut.model_validate(row) for row in rows]

    def create_upload_url(
        self,
        *,
        workspace: Workspace,
        project_id: UUID,
        payload: DraftUploadUrlRequest,
    ) -> DraftUploadUrlOut:
        project = require_owned_project(self.db, workspace=workspace, project_id=project_id)
        name = self._validate_name(payload.name)
        mime_type = self._validate_mime(payload.mime_type)
        size_bytes = self._validate_size(payload.size_bytes)
        self._ensure_file_limit(project.id)

        file_id = uuid4()
        storage_path = self._draft_storage_path(
            workspace_id=workspace.id,
            project_id=project.id,
            file_id=file_id,
            name=name,
        )
        signed = self.storage.create_signed_upload_url(storage_path=storage_path)
        expires_at = signed.expires_at
        # Opaque confirm handle: never embed storage paths (reconstruct server-side).
        token = self._encode_upload_token(
            {
                "typ": "draft_upload_intent",
                "fid": str(file_id),
                "pid": str(project.id),
                "wid": str(workspace.id),
                "name": name,
                "mime": mime_type,
                "size": size_bytes,
                "exp": int(expires_at.timestamp()),
            }
        )
        return DraftUploadUrlOut(
            upload_url=signed.upload_url,
            token=token,
            expires_at=expires_at,
        )

    def confirm_upload(
        self,
        *,
        workspace: Workspace,
        user: User,
        project_id: UUID,
        payload: DraftConfirmUploadRequest,
    ) -> DraftFileOut:
        project = require_owned_project(self.db, workspace=workspace, project_id=project_id)
        intent = self._decode_upload_token(payload.token)

        name = self._validate_name(payload.name)
        mime_type = self._validate_mime(payload.mime_type)
        size_bytes = self._validate_size(payload.size_bytes)

        if (
            intent["pid"] != str(project.id)
            or intent["wid"] != str(workspace.id)
            or intent["name"] != name
            or intent["mime"] != mime_type
            or int(intent["size"]) != size_bytes
        ):
            raise AppError(
                status_code=400,
                code="upload_mismatch",
                message="Upload metadata does not match the upload intent",
            )

        file_id = UUID(str(intent["fid"]))
        storage_path = self._draft_storage_path(
            workspace_id=UUID(str(intent["wid"])),
            project_id=UUID(str(intent["pid"])),
            file_id=file_id,
            name=str(intent["name"]),
        )

        existing = self.files.get_by_storage_path(storage_path=storage_path)
        if existing is not None:
            return DraftFileOut.model_validate(existing)

        self._ensure_file_limit(project.id)

        info = self.storage.get_object_info(storage_path=storage_path)
        if not info.exists:
            raise AppError(
                status_code=400,
                code="upload_not_found",
                message="Uploaded object was not found",
            )
        if info.size_bytes is not None and info.size_bytes != size_bytes:
            self.storage.delete_object(storage_path=storage_path)
            raise AppError(
                status_code=400,
                code="upload_mismatch",
                message="Uploaded object size does not match the upload intent",
            )
        if info.content_type:
            normalized = info.content_type.split(";")[0].strip().lower()
            if normalized and normalized != mime_type.lower():
                self.storage.delete_object(storage_path=storage_path)
                raise AppError(
                    status_code=400,
                    code="upload_mismatch",
                    message="Uploaded object type does not match the upload intent",
                )

        self.drafts.get_or_create(project_id=project.id)
        row = self.files.create(
            file_id=file_id,
            project_id=project.id,
            name=name,
            storage_path=storage_path,
            mime_type=mime_type,
            size_bytes=size_bytes,
            uploaded_by_user_id=user.id,
        )
        self.drafts.touch(project_id=project.id)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Unable to save draft file metadata",
            )
        self.db.refresh(row)
        return DraftFileOut.model_validate(row)

    def create_download_url(
        self,
        *,
        workspace: Workspace,
        project_id: UUID,
        file_id: UUID,
    ) -> DownloadUrlOut:
        project = require_owned_project(self.db, workspace=workspace, project_id=project_id)
        row = self.files.get_for_project(project_id=project.id, file_id=file_id)
        if row is None:
            raise AppError(status_code=404, code="not_found", message="File not found")
        signed = self.storage.create_signed_download_url(storage_path=row.storage_path)
        return DownloadUrlOut(
            download_url=signed.download_url,
            expires_at=signed.expires_at,
            name=row.name,
        )

    def delete_file(
        self,
        *,
        workspace: Workspace,
        project_id: UUID,
        file_id: UUID,
    ) -> dict:
        project = require_owned_project(self.db, workspace=workspace, project_id=project_id)
        row = self.files.get_for_project(project_id=project.id, file_id=file_id)
        if row is None:
            raise AppError(status_code=404, code="not_found", message="File not found")

        storage_path = row.storage_path
        self.storage.delete_object(storage_path=storage_path)
        self.files.delete(row)
        self.drafts.touch(project_id=project.id)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Unable to delete draft file metadata",
            )
        return {"ok": True}

    def list_resources(
        self, *, workspace: Workspace, project_id: UUID
    ) -> list[DraftResourceOut]:
        project = require_owned_project(self.db, workspace=workspace, project_id=project_id)
        items = self.resources.list_for_project(project_id=project.id)
        return [DraftResourceOut.model_validate(item) for item in items]

    def create_resource(
        self,
        *,
        workspace: Workspace,
        project_id: UUID,
        payload: DraftResourceCreateRequest,
    ) -> DraftResourceOut:
        project = require_owned_project(self.db, workspace=workspace, project_id=project_id)
        position = (
            payload.position
            if payload.position is not None
            else self.resources.next_position(project_id=project.id)
        )
        self.drafts.get_or_create(project_id=project.id)
        resource = self.resources.create(
            project_id=project.id,
            title=payload.title,
            url=payload.url,
            resource_type=ResourceType(payload.type.value),
            description=payload.description,
            position=position,
        )
        self.drafts.touch(project_id=project.id)
        self.db.commit()
        self.db.refresh(resource)
        return DraftResourceOut.model_validate(resource)

    def update_resource(
        self,
        *,
        workspace: Workspace,
        project_id: UUID,
        resource_id: UUID,
        payload: DraftResourceUpdateRequest,
    ) -> DraftResourceOut:
        if (
            payload.title is None
            and payload.url is None
            and payload.type is None
            and "description" not in payload.model_fields_set
            and payload.position is None
        ):
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

        project = require_owned_project(self.db, workspace=workspace, project_id=project_id)
        resource = self.resources.get_for_project(
            project_id=project.id, resource_id=resource_id
        )
        if resource is None:
            raise AppError(status_code=404, code="not_found", message="Resource not found")

        if payload.title is not None:
            resource.title = payload.title
        if payload.url is not None:
            resource.url = payload.url
        if payload.type is not None:
            resource.type = ResourceType(payload.type.value)
        if "description" in payload.model_fields_set:
            resource.description = payload.description
        if payload.position is not None:
            resource.position = payload.position

        self.resources.save(resource)
        self.drafts.touch(project_id=project.id)
        self.db.commit()
        self.db.refresh(resource)
        return DraftResourceOut.model_validate(resource)

    def delete_resource(
        self,
        *,
        workspace: Workspace,
        project_id: UUID,
        resource_id: UUID,
    ) -> dict:
        project = require_owned_project(self.db, workspace=workspace, project_id=project_id)
        resource = self.resources.get_for_project(
            project_id=project.id, resource_id=resource_id
        )
        if resource is None:
            raise AppError(status_code=404, code="not_found", message="Resource not found")
        self.resources.delete(resource)
        self.drafts.touch(project_id=project.id)
        self.db.commit()
        return {"ok": True}

    def _ensure_file_limit(self, project_id: UUID) -> None:
        count = self.files.count_for_project(project_id=project_id)
        if count >= DRAFT_FILES_MAX_PER_PROJECT:
            raise AppError(
                status_code=409,
                code="file_limit_reached",
                message="This project already has the maximum number of draft files",
            )

    def _validate_name(self, name: str) -> str:
        cleaned = name.strip()
        if not cleaned or len(cleaned) > DRAFT_FILE_NAME_MAX:
            raise AppError(
                status_code=400,
                code="validation_error",
                message="Request failed validation",
                details=[
                    {
                        "field": "name",
                        "message": f"Name must be 1–{DRAFT_FILE_NAME_MAX} characters",
                        "code": "length",
                    }
                ],
            )
        return cleaned

    def _validate_mime(self, mime_type: str) -> str:
        normalized = mime_type.strip().lower()
        if normalized not in DRAFT_FILE_MIME_ALLOWLIST:
            raise AppError(
                status_code=415,
                code="unsupported_media_type",
                message="This file type is not supported",
            )
        return normalized

    def _validate_size(self, size_bytes: int) -> int:
        if size_bytes < 1:
            raise AppError(
                status_code=400,
                code="validation_error",
                message="Request failed validation",
                details=[
                    {
                        "field": "size_bytes",
                        "message": "Size must be at least 1 byte",
                        "code": "range",
                    }
                ],
            )
        if size_bytes > DRAFT_FILE_MAX_BYTES:
            raise AppError(
                status_code=413,
                code="file_too_large",
                message="File exceeds the 25 MiB limit",
            )
        return size_bytes

    @staticmethod
    def _draft_storage_path(
        *,
        workspace_id: UUID,
        project_id: UUID,
        file_id: UUID,
        name: str,
    ) -> str:
        return f"{workspace_id}/{project_id}/draft/{file_id}/{safe_filename(name)}"

    def _encode_upload_token(self, payload: dict) -> str:
        return jwt.encode(payload, self.settings.upload_signing_secret, algorithm="HS256")

    def _decode_upload_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                self.settings.upload_signing_secret,
                algorithms=["HS256"],
                options={
                    "require": [
                        "exp",
                        "typ",
                        "fid",
                        "pid",
                        "wid",
                        "name",
                        "mime",
                        "size",
                    ]
                },
            )
        except jwt.ExpiredSignatureError as exc:
            raise AppError(
                status_code=400,
                code="upload_not_found",
                message="Upload intent has expired",
            ) from exc
        except jwt.PyJWTError as exc:
            raise AppError(
                status_code=400,
                code="upload_not_found",
                message="Upload intent is invalid",
            ) from exc

        if payload.get("typ") != "draft_upload_intent":
            raise AppError(
                status_code=400,
                code="upload_not_found",
                message="Upload intent is invalid",
            )
        # Reject legacy tokens that embedded storage paths.
        if "path" in payload:
            raise AppError(
                status_code=400,
                code="upload_not_found",
                message="Upload intent is invalid",
            )
        return payload
