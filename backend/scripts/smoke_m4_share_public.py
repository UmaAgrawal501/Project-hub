"""M4 share + public portal smoke tests (service-level, real DB + fake storage).

Run from backend/:
  python -m scripts.smoke_m4_share_public
"""

from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.database.session import get_session_factory
from app.models import (
    DraftFile,
    Project,
    ProjectDraft,
    ProjectStatus,
    User,
    Workspace,
)
from app.schemas.versions import PublishRequest
from app.services.publish_service import PublishService
from app.services.share_service import ShareService
from app.storage.supabase_storage import ObjectInfo, SignedDownload, SignedUpload


@dataclass
class FakeStorage:
    objects: dict[str, bytes] = field(default_factory=dict)

    def ensure_private_bucket(self) -> None:
        return None

    def create_signed_upload_url(self, *, storage_path: str) -> SignedUpload:
        return SignedUpload(
            upload_url=f"https://example.test/upload/{storage_path}",
            expires_at=datetime.now(timezone.utc),
        )

    def create_signed_download_url(self, *, storage_path: str) -> SignedDownload:
        return SignedDownload(
            download_url=f"https://example.test/dl/{storage_path}",
            expires_at=datetime.now(timezone.utc),
        )

    def get_object_info(self, *, storage_path: str) -> ObjectInfo:
        if storage_path not in self.objects:
            return ObjectInfo(size_bytes=None, content_type=None, exists=False)
        return ObjectInfo(
            size_bytes=len(self.objects[storage_path]),
            content_type="application/pdf",
            exists=True,
        )

    def delete_object(self, *, storage_path: str) -> None:
        self.objects.pop(storage_path, None)

    def copy_object(self, *, source_path: str, dest_path: str) -> None:
        if source_path not in self.objects:
            raise AppError(
                status_code=500,
                code="internal_error",
                message="missing source",
            )
        self.objects[dest_path] = self.objects[source_path]


def _seed(db: Session) -> tuple[User, Workspace, Project]:
    user_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    project_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"m4-{user_id.hex[:8]}@example.com",
        display_name="M4 Smoke",
    )
    workspace = Workspace(id=workspace_id, owner_user_id=user_id, name="Personal")
    project = Project(
        id=project_id,
        workspace_id=workspace_id,
        name="Portal Project",
        status=ProjectStatus.active,
        latest_version_number=None,
    )
    draft = ProjectDraft(project_id=project_id, overview="Published overview v1")
    db.add_all([user, workspace, project, draft])
    db.commit()
    db.refresh(user)
    db.refresh(workspace)
    db.refresh(project)
    return user, workspace, project


def _add_draft_file(
    db: Session,
    storage: FakeStorage,
    *,
    workspace: Workspace,
    project: Project,
    user: User,
) -> DraftFile:
    file_id = uuid.uuid4()
    path = f"{workspace.id}/{project.id}/draft/{file_id}/brief.pdf"
    storage.objects[path] = b"%PDF-m4"
    row = DraftFile(
        id=file_id,
        project_id=project.id,
        name="brief.pdf",
        storage_path=path,
        mime_type="application/pdf",
        size_bytes=len(storage.objects[path]),
        uploaded_by_user_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def main() -> None:
    db = get_session_factory()()
    storage = FakeStorage()
    settings = get_settings()
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if cond:
            print(f"PASS  {name}")
        else:
            failures.append(name)
            print(f"FAIL  {name} {detail}")

    try:
        user, workspace, project = _seed(db)
        publish = PublishService(db, settings, storage)  # type: ignore[arg-type]
        share = ShareService(db, storage)  # type: ignore[arg-type]

        # Never published → enable fails (links are minted on publish)
        try:
            share.enable_share(workspace=workspace, project_id=project.id)
            check("never published → enable conflict", False)
        except AppError as exc:
            check(
                "never published → enable conflict",
                exc.status_code == 409 and exc.code == "conflict",
                f"{exc.status_code} {exc.code}",
            )

        draft_file = _add_draft_file(
            db, storage, workspace=workspace, project=project, user=user
        )
        v1 = publish.publish(
            workspace=workspace,
            user=user,
            project_id=project.id,
            payload=PublishRequest(release_notes="Version one"),
        )
        check("publish returns share", v1.share is not None and v1.share.version_number == 1)
        token_v1 = v1.share.token

        # Mutate draft after publish — must not leak to portal
        draft = db.get(ProjectDraft, project.id)
        assert draft is not None
        draft.overview = "SECRET DRAFT OVERVIEW"
        db.add(draft)
        db.commit()

        portal = share.get_public_portal(token=token_v1)
        check("v1 portal loads", portal.version.version_number == 1)
        check(
            "portal name from version snapshot",
            portal.project.name == "Portal Project"
            and portal.version.name == "Portal Project",
        )
        check(
            "draft overview never in public",
            portal.version.overview == "Published overview v1"
            and "SECRET" not in (portal.version.overview or ""),
        )
        check(
            "no draft file id in public files",
            all(f.id != draft_file.id for f in portal.files),
        )
        check("versions_available locked to one", len(portal.versions_available) == 1)

        # Second version → new link; old link stays on v1
        draft.overview = "Published overview v2"
        db.add(draft)
        project.name = "Renamed Live"
        db.add(project)
        db.commit()
        v2 = publish.publish(
            workspace=workspace,
            user=user,
            project_id=project.id,
            payload=PublishRequest(release_notes="Version two"),
        )
        check("v2 share is new token", v2.share.token != token_v1)
        check("v2 share version", v2.share.version_number == 2)
        token_v2 = v2.share.token

        still_v1 = share.get_public_portal(token=token_v1)
        check("old link stays on v1", still_v1.version.version_number == 1)
        check(
            "old link keeps v1 name/overview",
            still_v1.version.name == "Portal Project"
            and still_v1.version.overview == "Published overview v1",
        )

        latest = share.get_public_portal(token=token_v2)
        check("new link is v2", latest.version.version_number == 2)
        check(
            "new link name is v2 snapshot (renamed)",
            latest.project.name == "Renamed Live",
        )
        try:
            share.get_public_portal_version(token=token_v2, version_number=1)
            check("locked token cannot open other version", False)
        except AppError as exc:
            check(
                "locked token cannot open other version",
                exc.code == "share_unavailable",
                exc.code,
            )
        check(
            "live status on portal",
            latest.project.status.value == "active",
        )

        listed = share.list_shares(workspace=workspace, project_id=project.id)
        check("list shares has two", len(listed) == 2)
        check(
            "list shares newest first",
            listed[0].version_number == 2 and listed[1].version_number == 1,
        )

        # Completed still public
        project.status = ProjectStatus.completed
        db.add(project)
        db.commit()
        completed_portal = share.get_public_portal(token=token_v2)
        check(
            "completed project still public",
            completed_portal.project.status.value == "completed",
        )

        # Archived still public
        project.status = ProjectStatus.archived
        db.add(project)
        db.commit()
        archived_portal = share.get_public_portal(token=token_v2)
        check(
            "archived project still public",
            archived_portal.project.status.value == "archived",
        )

        # Disable kills all links
        disabled = share.disable_share(workspace=workspace, project_id=project.id)
        check("disable share", disabled.enabled is False)
        for label, tok in (("v1", token_v1), ("v2", token_v2)):
            try:
                share.get_public_portal(token=tok)
                check(f"disabled {label} → share_unavailable", False)
            except AppError as exc:
                check(
                    f"disabled {label} → share_unavailable",
                    exc.code == "share_unavailable",
                    exc.code,
                )

        # Regenerate rotates only latest (v2); re-enables it
        regen = share.regenerate_share(workspace=workspace, project_id=project.id)
        check(
            "regenerate token",
            regen.enabled is True and regen.share.token != token_v2,
        )
        try:
            share.get_public_portal(token=token_v2)
            check("old latest token dead", False)
        except AppError as exc:
            check("old latest token dead", exc.code == "share_unavailable", exc.code)
        new_token = regen.share.token
        check(
            "new latest token works",
            share.get_public_portal(token=new_token).version.version_number == 2,
        )
        # Re-enable v1 for remaining checks (disable turned it off)
        share.enable_share(workspace=workspace, project_id=project.id)
        # enable only flips latest — re-enable v1 manually via DB for old-link check? 
        # After disable-all, v1 stays disabled. Regenerate only enables latest.
        # Re-enable all: enable only touches latest. For smoke, flip v1 enabled via service repo.
        from app.repositories.share_repository import ShareRepository

        repo = ShareRepository(db)
        v1_share = repo.get_for_version(project_id=project.id, version_number=1)
        assert v1_share is not None
        v1_share.is_enabled = True
        repo.save(v1_share)
        db.commit()
        check(
            "v1 token still works after latest regen",
            share.get_public_portal(token=token_v1).version.version_number == 1,
        )

        # Invalid token
        try:
            share.get_public_portal(token="not-a-real-token")
            check("invalid token", False)
        except AppError as exc:
            check("invalid token", exc.code == "share_unavailable", exc.code)

        # Public download (locked version only)
        file_id = v2.files[0].id
        dl = share.create_public_download_url(token=new_token, file_id=file_id)
        check("public file download", "https://example.test/dl/" in dl.download_url)
        try:
            share.create_public_download_url(
                token=new_token, file_id=v1.files[0].id, version_number=1
            )
            check("public download wrong version blocked", False)
        except AppError as exc:
            check(
                "public download wrong version blocked",
                exc.code == "share_unavailable",
                exc.code,
            )
        dl_v1 = share.create_public_download_url(
            token=token_v1, file_id=v1.files[0].id, version_number=1
        )
        check("public download via v1 token", dl_v1.name == "brief.pdf")

        # Draft file id must not authorize on public
        try:
            share.create_public_download_url(
                token=new_token, file_id=draft_file.id, version_number=2
            )
            check("draft file id never authorizes", False)
        except AppError as exc:
            check(
                "draft file id never authorizes",
                exc.code == "share_unavailable",
                exc.code,
            )

        # Owner version download
        owner_dl = publish.create_version_download_url(
            workspace=workspace,
            project_id=project.id,
            version_number=2,
            file_id=file_id,
        )
        check(
            "owner version download",
            "https://example.test/dl/" in owner_dl.download_url,
        )

        # Soft-deleted unavailable
        project.deleted_at = datetime.now(timezone.utc)
        db.add(project)
        db.commit()
        try:
            share.get_public_portal(token=new_token)
            check("soft-deleted project unavailable", False)
        except AppError as exc:
            check(
                "soft-deleted project unavailable",
                exc.code == "share_unavailable",
                exc.code,
            )

        dumped = archived_portal.model_dump()
        check(
            "public payload has contract keys only",
            set(dumped.keys())
            == {"project", "version", "resources", "files", "versions_available"},
        )
        check(
            "project chrome keys only name+status",
            set(dumped["project"].keys()) == {"name", "status"},
        )

    finally:
        db.close()

    if failures:
        print(f"\n{len(failures)} failure(s): {failures}")
        sys.exit(1)
    print("\nAll M4 smoke checks passed.")


if __name__ == "__main__":
    main()
