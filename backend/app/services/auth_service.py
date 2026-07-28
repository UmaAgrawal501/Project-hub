from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.models import User, Workspace
from app.repositories.user_repository import UserRepository, WorkspaceRepository
from app.schemas.auth import (
    AuthSuccessData,
    ChangePasswordRequest,
    ForgotPasswordData,
    MeData,
    OkData,
    ResetPasswordRequest,
    SessionOut,
    SignInRequest,
    SignUpRequest,
    UpdateMeRequest,
    UserOut,
    WorkspaceOut,
)
from app.services.supabase_auth import SupabaseAuthClient


class AuthService:
    def __init__(self, db: Session, auth_client: SupabaseAuthClient, settings: Settings) -> None:
        self.db = db
        self.auth_client = auth_client
        self.settings = settings
        self.users = UserRepository(db)
        self.workspaces = WorkspaceRepository(db)

    def sign_up(self, payload: SignUpRequest) -> AuthSuccessData:
        existing = self.users.get_by_email(payload.email)
        if existing is not None:
            raise AppError(status_code=409, code="email_taken", message="Email is already registered")

        auth_response = self.auth_client.sign_up(
            email=str(payload.email),
            password=payload.password,
            display_name=payload.display_name,
        )
        user_id = self._user_id_from_auth_response(auth_response)

        user = self.users.create(
            user_id=user_id,
            email=str(payload.email),
            display_name=payload.display_name,
        )
        workspace = self.workspaces.create(owner_user_id=user.id)
        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(workspace)

        # Admin create does not return a session; sign in for tokens.
        session_response = self.auth_client.sign_in(
            email=str(payload.email),
            password=payload.password,
        )
        session = self._require_session(session_response)

        return AuthSuccessData(
            user=UserOut.model_validate(user),
            workspace=WorkspaceOut.model_validate(workspace),
            session=session,
        )

    def sign_in(self, payload: SignInRequest) -> AuthSuccessData:
        auth_response = self.auth_client.sign_in(
            email=str(payload.email),
            password=payload.password,
        )
        session = self._require_session(auth_response)
        user_id = self._user_id_from_auth_response(auth_response)
        user, workspace = self._require_profile(user_id)
        return AuthSuccessData(
            user=UserOut.model_validate(user),
            workspace=WorkspaceOut.model_validate(workspace),
            session=session,
        )

    def sign_out(self, *, access_token: str) -> OkData:
        self.auth_client.sign_out(access_token=access_token)
        return OkData(ok=True)

    def me(self, *, user: User, workspace: Workspace) -> MeData:
        return MeData(
            user=UserOut.model_validate(user),
            workspace=WorkspaceOut.model_validate(workspace),
        )

    def update_me(self, *, user: User, payload: UpdateMeRequest) -> dict:
        updated = self.users.update_display_name(user, payload.display_name)
        self.db.commit()
        self.db.refresh(updated)
        return {"user": UserOut.model_validate(updated)}

    def forgot_password(self, *, email: str) -> ForgotPasswordData:
        # Always return the same shape (anti-enumeration).
        self.auth_client.recover_password(email=email)
        return ForgotPasswordData()

    def reset_password(self, payload: ResetPasswordRequest) -> OkData:
        # `token` is the recovery session access_token from the reset email redirect.
        self.auth_client.update_password_with_access_token(
            access_token=payload.token,
            password=payload.password,
        )
        return OkData(ok=True)

    def change_password(
        self,
        *,
        user: User,
        access_token: str,
        payload: ChangePasswordRequest,
    ) -> OkData:
        # Verify current password by attempting sign-in.
        self.auth_client.sign_in(email=user.email, password=payload.current_password)
        self.auth_client.update_password_with_access_token(
            access_token=access_token,
            password=payload.new_password,
        )
        return OkData(ok=True)

    def _require_profile(self, user_id: UUID) -> tuple[User, Workspace]:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise AppError(status_code=401, code="unauthorized", message="Authentication required")
        workspace = self.workspaces.get_by_owner(user.id)
        if workspace is None:
            raise AppError(status_code=401, code="unauthorized", message="Authentication required")
        return user, workspace

    def _user_id_from_auth_response(self, auth_response: dict) -> UUID:
        # Admin create returns the user object at the top level; password grant nests under "user".
        user_payload = auth_response.get("user") or auth_response
        user_id = user_payload.get("id")
        if not user_id:
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Authentication provider returned an incomplete user",
            )
        return UUID(str(user_id))

    def _session_from_auth_response(self, auth_response: dict) -> SessionOut | None:
        access_token = auth_response.get("access_token")
        refresh_token = auth_response.get("refresh_token")
        expires_in = auth_response.get("expires_in")
        if not access_token or not refresh_token or expires_in is None:
            return None
        return SessionOut(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(expires_in),
            token_type=str(auth_response.get("token_type") or "bearer"),
        )

    def _require_session(self, auth_response: dict) -> SessionOut:
        session = self._session_from_auth_response(auth_response)
        if session is None:
            raise AppError(
                status_code=401,
                code="invalid_credentials",
                message="Invalid email or password",
            )
        return session
