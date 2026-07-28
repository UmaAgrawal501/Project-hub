from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import Settings
from app.core.errors import AppError


@dataclass(frozen=True)
class SignedUpload:
    upload_url: str
    expires_at: datetime


@dataclass(frozen=True)
class SignedDownload:
    download_url: str
    expires_at: datetime


@dataclass(frozen=True)
class ObjectInfo:
    size_bytes: int | None
    content_type: str | None
    exists: bool


class SupabaseStorageClient:
    """Supabase Storage REST client (service role; never exposed to browsers)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base = settings.supabase_url.rstrip("/") + "/storage/v1"
        self._bucket = settings.storage_bucket
        self._service_key = settings.supabase_service_role_key

    def _headers(self, *, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "apikey": self._service_key,
            "Authorization": f"Bearer {self._service_key}",
        }
        if extra:
            headers.update(extra)
        return headers

    def ensure_private_bucket(self) -> None:
        try:
            with httpx.Client(timeout=30.0) as client:
                get_resp = client.get(
                    f"{self._base}/bucket/{self._bucket}",
                    headers=self._headers(),
                )
                if get_resp.status_code == 200:
                    return
                if get_resp.status_code not in (400, 404):
                    self._raise_storage_error(get_resp, "Unable to access storage bucket")

                create_resp = client.post(
                    f"{self._base}/bucket",
                    headers=self._headers(extra={"Content-Type": "application/json"}),
                    json={
                        "id": self._bucket,
                        "name": self._bucket,
                        "public": False,
                        "file_size_limit": 25 * 1024 * 1024,
                    },
                )
                if create_resp.status_code in (200, 201):
                    return
                # Race: another process created it.
                if create_resp.status_code in (400, 409):
                    verify = client.get(
                        f"{self._base}/bucket/{self._bucket}",
                        headers=self._headers(),
                    )
                    if verify.status_code == 200:
                        return
                self._raise_storage_error(create_resp, "Unable to create storage bucket")
        except httpx.HTTPError as exc:
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Storage provider unavailable",
            ) from exc

    def create_signed_upload_url(self, *, storage_path: str) -> SignedUpload:
        self.ensure_private_bucket()
        encoded_path = quote(storage_path, safe="/")
        url = f"{self._base}/object/upload/sign/{self._bucket}/{encoded_path}"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    url,
                    headers=self._headers(
                        extra={
                            "Content-Type": "application/json",
                            "x-upsert": "false",
                        }
                    ),
                    json={},
                )
        except httpx.HTTPError as exc:
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Storage provider unavailable",
            ) from exc

        if response.status_code >= 400:
            self._raise_storage_error(response, "Unable to create upload URL")

        payload = self._json(response)
        relative = payload.get("url")
        if not isinstance(relative, str) or not relative:
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Storage provider returned an invalid upload URL",
            )

        if relative.startswith("http://") or relative.startswith("https://"):
            upload_url = relative
        else:
            upload_url = f"{self._base}{relative if relative.startswith('/') else '/' + relative}"

        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=self._settings.signed_upload_ttl_seconds
        )
        return SignedUpload(upload_url=upload_url, expires_at=expires_at)

    def create_signed_download_url(self, *, storage_path: str) -> SignedDownload:
        encoded_path = quote(storage_path, safe="/")
        url = f"{self._base}/object/sign/{self._bucket}/{encoded_path}"
        expires_in = self._settings.signed_download_ttl_seconds
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    url,
                    headers=self._headers(extra={"Content-Type": "application/json"}),
                    json={"expiresIn": expires_in},
                )
        except httpx.HTTPError as exc:
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Storage provider unavailable",
            ) from exc

        if response.status_code >= 400:
            self._raise_storage_error(response, "Unable to create download URL")

        payload = self._json(response)
        signed = payload.get("signedURL") or payload.get("signedUrl")
        if not isinstance(signed, str) or not signed:
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Storage provider returned an invalid download URL",
            )

        if signed.startswith("http://") or signed.startswith("https://"):
            download_url = signed
        else:
            download_url = f"{self._base}{signed if signed.startswith('/') else '/' + signed}"

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return SignedDownload(download_url=download_url, expires_at=expires_at)

    def get_object_info(self, *, storage_path: str) -> ObjectInfo:
        encoded_path = quote(storage_path, safe="/")
        url = f"{self._base}/object/info/{self._bucket}/{encoded_path}"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=self._headers())
        except httpx.HTTPError as exc:
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Storage provider unavailable",
            ) from exc

        if response.status_code == 404:
            return ObjectInfo(size_bytes=None, content_type=None, exists=False)
        if response.status_code >= 400:
            # Fallback: HEAD object endpoint
            return self._head_object(storage_path=storage_path)

        payload = self._json(response)
        size = payload.get("metadata", {}).get("size") if isinstance(payload.get("metadata"), dict) else None
        if size is None:
            size = payload.get("size") or payload.get("contentLength")
        content_type = None
        if isinstance(payload.get("metadata"), dict):
            content_type = payload["metadata"].get("mimetype") or payload["metadata"].get("contentType")
        content_type = content_type or payload.get("contentType") or payload.get("mimetype")
        try:
            size_int = int(size) if size is not None else None
        except (TypeError, ValueError):
            size_int = None
        return ObjectInfo(size_bytes=size_int, content_type=content_type, exists=True)

    def _head_object(self, *, storage_path: str) -> ObjectInfo:
        encoded_path = quote(storage_path, safe="/")
        url = f"{self._base}/object/{self._bucket}/{encoded_path}"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.head(url, headers=self._headers())
        except httpx.HTTPError as exc:
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Storage provider unavailable",
            ) from exc

        if response.status_code == 404:
            return ObjectInfo(size_bytes=None, content_type=None, exists=False)
        if response.status_code >= 400:
            self._raise_storage_error(response, "Unable to verify uploaded object")

        size_header = response.headers.get("content-length")
        try:
            size_int = int(size_header) if size_header is not None else None
        except ValueError:
            size_int = None
        return ObjectInfo(
            size_bytes=size_int,
            content_type=response.headers.get("content-type"),
            exists=True,
        )

    def delete_object(self, *, storage_path: str) -> None:
        """Delete object. Missing object is treated as success."""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    "DELETE",
                    f"{self._base}/object/{self._bucket}",
                    headers=self._headers(extra={"Content-Type": "application/json"}),
                    json={"prefixes": [storage_path]},
                )
        except httpx.HTTPError as exc:
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Storage provider unavailable",
            ) from exc

        if response.status_code in (200, 204):
            return
        # Some deployments return 404 when nothing to delete.
        if response.status_code == 404:
            return
        self._raise_storage_error(response, "Unable to delete storage object")

    def copy_object(self, *, source_path: str, dest_path: str) -> None:
        """Copy object within the private bucket (immutable version publish)."""
        self.ensure_private_bucket()
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self._base}/object/copy",
                    headers=self._headers(extra={"Content-Type": "application/json"}),
                    json={
                        "bucketId": self._bucket,
                        "sourceKey": source_path,
                        "destinationKey": dest_path,
                    },
                )
                if response.status_code in (200, 201):
                    return
                # Fallback: download + re-upload if copy endpoint unavailable.
                if response.status_code in (404, 405, 501):
                    self._copy_via_download_upload(
                        client=client,
                        source_path=source_path,
                        dest_path=dest_path,
                    )
                    return
                self._raise_storage_error(response, "Unable to copy storage object")
        except httpx.HTTPError as exc:
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Storage provider unavailable",
            ) from exc

    def _copy_via_download_upload(
        self,
        *,
        client: httpx.Client,
        source_path: str,
        dest_path: str,
    ) -> None:
        src = quote(source_path, safe="/")
        dst = quote(dest_path, safe="/")
        get_resp = client.get(
            f"{self._base}/object/{self._bucket}/{src}",
            headers=self._headers(),
        )
        if get_resp.status_code == 404:
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Draft file object missing during publish",
            )
        if get_resp.status_code >= 400:
            self._raise_storage_error(get_resp, "Unable to read draft file for publish")

        content_type = get_resp.headers.get("content-type") or "application/octet-stream"
        put_resp = client.post(
            f"{self._base}/object/{self._bucket}/{dst}",
            headers=self._headers(
                extra={
                    "Content-Type": content_type,
                    "x-upsert": "false",
                }
            ),
            content=get_resp.content,
        )
        if put_resp.status_code in (200, 201):
            return
        self._raise_storage_error(put_resp, "Unable to write version file object")

    def _json(self, response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Invalid response from storage provider",
            ) from exc
        if not isinstance(payload, dict):
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Invalid response from storage provider",
            )
        return payload

    def _raise_storage_error(self, response: httpx.Response, fallback: str) -> None:
        message = fallback
        try:
            payload = response.json()
            message = str(payload.get("message") or payload.get("error") or fallback)
        except ValueError:
            pass
        raise AppError(status_code=500, code="internal_error", message=message)
