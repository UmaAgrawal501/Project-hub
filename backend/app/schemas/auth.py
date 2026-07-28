from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def to_iso_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    return dt.astimezone().isoformat().replace("+00:00", "Z")


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserOut(APIModel):
    id: UUID
    email: EmailStr
    display_name: str
    created_at: datetime
    updated_at: datetime


class WorkspaceOut(APIModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class SessionOut(APIModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


class SignUpRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("display_name", mode="before")
    @classmethod
    def strip_display_name(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Display name is required")
        return cleaned


class SignInRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    password: str = Field(min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class UpdateMeRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)

    @field_validator("display_name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Display name is required")
        return cleaned


class AuthSuccessData(APIModel):
    user: UserOut
    workspace: WorkspaceOut
    session: SessionOut


class MeData(APIModel):
    user: UserOut
    workspace: WorkspaceOut


class OkData(APIModel):
    ok: bool = True


class ForgotPasswordData(APIModel):
    ok: bool = True
    message: str = (
        "If an account exists for this email, a reset link has been sent."
    )


class DataEnvelope(APIModel):
    data: dict | list | UserOut | WorkspaceOut | AuthSuccessData | MeData | OkData | ForgotPasswordData
