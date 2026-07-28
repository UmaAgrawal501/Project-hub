from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.deps import CurrentUserContext, get_current_user, get_supabase_auth
from app.database.session import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    SignInRequest,
    SignUpRequest,
    UpdateMeRequest,
)
from app.services.auth_service import AuthService
from app.services.supabase_auth import SupabaseAuthClient

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(
    db: Session = Depends(get_db),
    auth_client: SupabaseAuthClient = Depends(get_supabase_auth),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    return AuthService(db=db, auth_client=auth_client, settings=settings)


@router.post("/sign-up", status_code=201)
def sign_up(payload: SignUpRequest, service: AuthService = Depends(get_auth_service)) -> dict:
    data = service.sign_up(payload)
    return {"data": data.model_dump(mode="json")}


@router.post("/sign-in")
def sign_in(payload: SignInRequest, service: AuthService = Depends(get_auth_service)) -> dict:
    data = service.sign_in(payload)
    return {"data": data.model_dump(mode="json")}


@router.post("/sign-out")
def sign_out(
    current: CurrentUserContext = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    data = service.sign_out(access_token=current.access_token)
    return {"data": data.model_dump(mode="json")}


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    data = service.forgot_password(email=str(payload.email))
    return {"data": data.model_dump(mode="json")}


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    data = service.reset_password(payload)
    return {"data": data.model_dump(mode="json")}


@router.get("/me")
def me(
    current: CurrentUserContext = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    data = service.me(user=current.user, workspace=current.workspace)
    return {"data": data.model_dump(mode="json")}


@router.patch("/me")
def update_me(
    payload: UpdateMeRequest,
    current: CurrentUserContext = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    data = service.update_me(user=current.user, payload=payload)
    return {
        "data": {
            "user": data["user"].model_dump(mode="json"),
        }
    }


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current: CurrentUserContext = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    data = service.change_password(
        user=current.user,
        access_token=current.access_token,
        payload=payload,
    )
    return {"data": data.model_dump(mode="json")}
