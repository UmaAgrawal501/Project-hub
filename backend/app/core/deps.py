import json
from functools import lru_cache
from uuid import UUID

import httpx
import jwt
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.database.session import get_db
from app.models import User, Workspace
from app.repositories.user_repository import UserRepository, WorkspaceRepository
from app.services.supabase_auth import SupabaseAuthClient


def get_supabase_auth(settings: Settings = Depends(get_settings)) -> SupabaseAuthClient:
    return SupabaseAuthClient(settings)


@lru_cache
def _fetch_jwks(supabase_url: str, anon_key: str) -> dict:
    url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(url, headers={"apikey": anon_key, "Authorization": f"Bearer {anon_key}"})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        raise AppError(
            status_code=500,
            code="internal_error",
            message="Unable to validate authentication token",
        ) from exc


def _signing_key_for_token(token: str, settings: Settings):
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    jwks = _fetch_jwks(settings.supabase_url, settings.supabase_anon_key)
    for jwk in jwks.get("keys", []):
        if jwk.get("kid") == kid:
            return jwt.algorithms.ECAlgorithm.from_jwk(json.dumps(jwk))
    # Refresh once if kid not found (key rotation).
    _fetch_jwks.cache_clear()
    jwks = _fetch_jwks(settings.supabase_url, settings.supabase_anon_key)
    for jwk in jwks.get("keys", []):
        if jwk.get("kid") == kid:
            return jwt.algorithms.ECAlgorithm.from_jwk(json.dumps(jwk))
    raise AppError(status_code=401, code="unauthorized", message="Authentication required")


def _extract_bearer(authorization: str | None) -> str:
    if not authorization:
        raise AppError(status_code=401, code="unauthorized", message="Authentication required")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AppError(status_code=401, code="unauthorized", message="Authentication required")
    return token


def decode_access_token(token: str, settings: Settings) -> UUID:
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")
        if alg.startswith("ES") or alg.startswith("RS"):
            key = _signing_key_for_token(token, settings)
            payload = jwt.decode(
                token,
                key=key,
                algorithms=[alg],
                audience="authenticated",
            )
        else:
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
    except jwt.PyJWTError as exc:
        raise AppError(status_code=401, code="unauthorized", message="Authentication required") from exc

    sub = payload.get("sub")
    if not sub:
        raise AppError(status_code=401, code="unauthorized", message="Authentication required")
    try:
        return UUID(str(sub))
    except ValueError as exc:
        raise AppError(status_code=401, code="unauthorized", message="Authentication required") from exc


class CurrentUserContext:
    def __init__(self, user: User, workspace: Workspace, access_token: str) -> None:
        self.user = user
        self.workspace = workspace
        self.access_token = access_token


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CurrentUserContext:
    token = _extract_bearer(authorization)
    user_id = decode_access_token(token, settings)
    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise AppError(status_code=401, code="unauthorized", message="Authentication required")
    workspace = WorkspaceRepository(db).get_by_owner(user.id)
    if workspace is None:
        raise AppError(status_code=401, code="unauthorized", message="Authentication required")
    return CurrentUserContext(user=user, workspace=workspace, access_token=token)
