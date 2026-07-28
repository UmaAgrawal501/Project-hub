from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import AppError


class SupabaseAuthClient:
    """Thin HTTP client for Supabase Auth (GoTrue) REST API."""

    def __init__(self, settings: Settings) -> None:
        self._base = settings.supabase_url.rstrip("/") + "/auth/v1"
        self._anon_key = settings.supabase_anon_key
        self._service_key = settings.supabase_service_role_key
        self._reset_redirect = settings.password_reset_redirect_url

    def _headers(self, *, access_token: str | None = None, service_role: bool = False) -> dict[str, str]:
        key = self._service_key if service_role else self._anon_key
        headers = {
            "apikey": key,
            "Content-Type": "application/json",
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        elif service_role:
            headers["Authorization"] = f"Bearer {self._service_key}"
        else:
            headers["Authorization"] = f"Bearer {self._anon_key}"
        return headers

    def sign_up(self, *, email: str, password: str, display_name: str) -> dict[str, Any]:
        """Create a confirmed user via Admin API (V1: no email verification gate)."""
        payload = {
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"display_name": display_name},
        }
        return self._request("POST", "/admin/users", json=payload, service_role=True)

    def public_sign_up(self, *, email: str, password: str, display_name: str) -> dict[str, Any]:
        payload = {
            "email": email,
            "password": password,
            "data": {"display_name": display_name},
        }
        return self._request("POST", "/signup", json=payload)

    def sign_in(self, *, email: str, password: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/token?grant_type=password",
            json={"email": email, "password": password},
        )

    def sign_out(self, *, access_token: str) -> None:
        self._request("POST", "/logout", access_token=access_token, allow_empty=True)

    def recover_password(self, *, email: str) -> None:
        self._request(
            "POST",
            "/recover",
            json={"email": email, "gotrue_meta_security": {}},
            params={"redirect_to": self._reset_redirect},
            allow_empty=True,
            ignore_user_errors=True,
        )

    def update_password_with_access_token(self, *, access_token: str, password: str) -> dict[str, Any]:
        return self._request(
            "PUT",
            "/user",
            json={"password": password},
            access_token=access_token,
        )

    def get_user(self, *, access_token: str) -> dict[str, Any]:
        return self._request("GET", "/user", access_token=access_token)

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        access_token: str | None = None,
        service_role: bool = False,
        allow_empty: bool = False,
        ignore_user_errors: bool = False,
    ) -> dict[str, Any]:
        url = f"{self._base}{path}"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method,
                    url,
                    headers=self._headers(access_token=access_token, service_role=service_role),
                    json=json,
                    params=params,
                )
        except httpx.HTTPError as exc:
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Authentication provider unavailable",
            ) from exc

        if ignore_user_errors and response.status_code >= 400:
            return {}

        if response.status_code >= 400:
            self._raise_for_auth_error(response)

        if allow_empty and not response.content:
            return {}

        try:
            return response.json()
        except ValueError as exc:
            if allow_empty:
                return {}
            raise AppError(
                status_code=500,
                code="internal_error",
                message="Invalid response from authentication provider",
            ) from exc

    def _raise_for_auth_error(self, response: httpx.Response) -> None:
        message = "Authentication request failed"
        code_hint = ""
        try:
            payload = response.json()
            message = payload.get("msg") or payload.get("error_description") or payload.get("error") or message
            code_hint = str(payload.get("error_code") or payload.get("error") or "")
        except ValueError:
            pass

        lower = f"{message} {code_hint}".lower()
        if response.status_code in (400, 422) and (
            "already" in lower or "registered" in lower or "exists" in lower
        ):
            raise AppError(status_code=409, code="email_taken", message="Email is already registered")
        if response.status_code in (400, 401) and (
            "invalid" in lower or "credentials" in lower or "password" in lower
        ):
            raise AppError(
                status_code=401,
                code="invalid_credentials",
                message="Invalid email or password",
            )
        if "token" in lower and response.status_code in (400, 401, 403):
            raise AppError(
                status_code=400,
                code="invalid_or_expired_token",
                message="Invalid or expired token",
            )
        if response.status_code == 429:
            raise AppError(status_code=429, code="rate_limited", message="Too many requests")
        raise AppError(
            status_code=500,
            code="internal_error",
            message="Authentication provider error",
        )
