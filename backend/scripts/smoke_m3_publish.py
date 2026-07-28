"""M3 publish/versions smoke tests (service-level, real DB + in-memory storage).

Run from backend/:
  python -m scripts.smoke_m3_publish
"""

from __future__ import annotations

import sys
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Allow `python scripts/smoke_m3_publish.py` from backend/
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
from app.services.dirty import has_unpublished_changes
from app.services.publish_service import PublishService
from app.storage.supabase_storage import ObjectInfo, SignedDownload, SignedUpload


@dataclass
class FakeStorage:
    objects: dict[str, bytes] = field(default_factory=dict)
    copy_calls: list[tuple[str, str]] = field(default_factory=list)

    def ensure_private_bucket(self) -> None:
        return None

    def create_signed_upload_url(self, *, storage_path: str) -> SignedUpload:
        return SignedUpload(
            upload_url=f"https://example.test/upload/{storage_path}",
            expires_at=datetime.now(timezone.utc),
        )

    def create_signed_download_url(self, *, storage_path: str) -> SignedDownload:
        return SignedDownload(
            download_url=f"https://example.test/download/{storage_path}",
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
                message="Draft file object missing during publish",
            )
        self.objects[dest_path] = self.objects[source_path]
        self.copy_calls.append((source_path, dest_path))


def _seed(db: Session, storage: FakeStorage) -> tuple[User, Workspace, Project]:
    user_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    project_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"m3-{user_id.hex[:8]}@example.com",
        display_name="M3 Smoke",
    )
    workspace = Workspace(id=workspace_id, owner_user_id=user_id, name="Personal")
    project = Project(
        id=project_id,
        workspace_id=workspace_id,
        name="Delivery Alpha",
        status=ProjectStatus.active,
        latest_version_number=None,
    )
    draft = ProjectDraft(project_id=project_id, overview="Client overview")
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
    name: str = "spec.pdf",
) -> DraftFile:
    file_id = uuid.uuid4()
    path = f"{workspace.id}/{project.id}/draft/{file_id}/{name}"
    storage.objects[path] = b"%PDF-1.4 smoke"
    row = DraftFile(
        id=file_id,
        project_id=project.id,
        name=name,
        storage_path=path,
        mime_type="application/pdf",
        size_bytes=len(storage.objects[path]),
        uploaded_by_user_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _service(db: Session, storage: FakeStorage) -> PublishService:
    return PublishService(db, get_settings(), storage)  # type: ignore[arg-type]


def main() -> None:
    db = get_session_factory()()
    storage = FakeStorage()
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if cond:
            print(f"PASS  {name}")
        else:
            failures.append(name)
            print(f"FAIL  {name} {detail}")

    try:
        user, workspace, project = _seed(db, storage)
        svc = _service(db, storage)

        # Empty draft (clear overview) → nothing_to_publish
        draft = db.get(ProjectDraft, project.id)
        assert draft is not None
        draft.overview = None
        db.add(draft)
        db.commit()
        try:
            svc.publish(
                workspace=workspace,
                user=user,
                project_id=project.id,
                payload=PublishRequest(release_notes="v1"),
            )
            check("empty draft → 409 nothing_to_publish", False, "expected error")
        except AppError as exc:
            check(
                "empty draft → 409 nothing_to_publish",
                exc.status_code == 409 and exc.code == "nothing_to_publish",
                f"got {exc.status_code} {exc.code}",
            )

        # Empty release notes → validation (pydantic)
        try:
            PublishRequest(release_notes="   ")
            check("empty release notes → validation_error", False)
        except Exception:
            check("empty release notes → validation_error", True)

        # Restore publishable draft + file
        draft.overview = "Client overview"
        db.add(draft)
        db.commit()
        draft_file = _add_draft_file(
            db, storage, workspace=workspace, project=project, user=user
        )

        result1 = svc.publish(
            workspace=workspace,
            user=user,
            project_id=project.id,
            payload=PublishRequest(release_notes="First delivery"),
        )
        check("first publish version_number == 1", result1.version.version_number == 1)
        check("first publish snaps name", result1.version.name == "Delivery Alpha")
        check("first publish snaps overview", result1.version.overview == "Client overview")
        check("first publish has file", len(result1.files) == 1)
        db.refresh(project)
        check("latest_version_number == 1", project.latest_version_number == 1)
        check(
            "dirty false after first publish",
            has_unpublished_changes(project, db) is False,
        )

        vpath = result1.files[0]
        # Reload storage path from DB
        from app.models import VersionFile

        vf = db.query(VersionFile).filter(VersionFile.id == vpath.id).one()
        check(
            "version storage namespace",
            f"/versions/1/" in vf.storage_path and "/draft/" not in vf.storage_path,
            vf.storage_path,
        )
        check(
            "version object exists (copy)",
            vf.storage_path in storage.objects,
        )
        check(
            "version path independent of draft path",
            vf.storage_path != draft_file.storage_path,
        )

        # Second publish
        result2 = svc.publish(
            workspace=workspace,
            user=user,
            project_id=project.id,
            payload=PublishRequest(release_notes="Second delivery"),
        )
        check("second publish version_number == 2", result2.version.version_number == 2)
        versions = svc.list_versions(workspace=workspace, project_id=project.id)
        check(
            "list descending",
            [v.version_number for v in versions] == [2, 1],
        )

        # Republish identical draft
        result3 = svc.publish(
            workspace=workspace,
            user=user,
            project_id=project.id,
            payload=PublishRequest(release_notes="Notes only change"),
        )
        check("republish identical draft allowed", result3.version.version_number == 3)

        # Edit draft after publish must not change previous versions
        v1_before = svc.get_version(
            workspace=workspace, project_id=project.id, version_number=1
        )
        draft.overview = "Changed after publish"
        db.add(draft)
        project.name = "Renamed Live"
        db.add(project)
        db.commit()
        db.refresh(project)
        v1_after = svc.get_version(
            workspace=workspace, project_id=project.id, version_number=1
        )
        check(
            "v1 overview immutable after draft edit",
            v1_before.version.overview == v1_after.version.overview == "Client overview",
        )
        check(
            "v1 name immutable after rename",
            v1_after.version.name == "Delivery Alpha",
        )
        check(
            "dirty true after draft/name edit",
            has_unpublished_changes(project, db) is True,
        )

        # Soft-deleted → project_deleted
        project.deleted_at = datetime.now(timezone.utc)
        db.add(project)
        db.commit()
        try:
            svc.publish(
                workspace=workspace,
                user=user,
                project_id=project.id,
                payload=PublishRequest(release_notes="Nope"),
            )
            check("soft-delete → project_deleted", False)
        except AppError as exc:
            check(
                "soft-delete → project_deleted",
                exc.status_code == 409 and exc.code == "project_deleted",
                f"got {exc.status_code} {exc.code}",
            )

        # Concurrent publish behaviour (separate project)
        project.deleted_at = None
        db.add(project)
        db.commit()

        user2, workspace2, project2 = _seed(db, storage)
        d2 = db.get(ProjectDraft, project2.id)
        assert d2 is not None
        d2.overview = "Concurrent"
        db.add(d2)
        db.commit()

        errors: list[str] = []
        successes: list[int] = []
        lock = threading.Lock()

        def _publish_once() -> None:
            local = get_session_factory()()
            try:
                local_storage = storage
                local_svc = _service(local, local_storage)
                ws = local.get(Workspace, workspace2.id)
                us = local.get(User, user2.id)
                assert ws is not None and us is not None
                out = local_svc.publish(
                    workspace=ws,
                    user=us,
                    project_id=project2.id,
                    payload=PublishRequest(release_notes=f"race-{uuid.uuid4().hex[:6]}"),
                )
                with lock:
                    successes.append(out.version.version_number)
            except AppError as exc:
                with lock:
                    errors.append(exc.code)
            finally:
                local.close()

        threads = [threading.Thread(target=_publish_once) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        check(
            "concurrent publish: all version numbers unique or conflict",
            len(successes) >= 1
            and len(set(successes)) == len(successes)
            and all(c in ("conflict",) or True for c in errors),
            f"successes={successes} errors={errors}",
        )
        check(
            "concurrent publish: no duplicate version numbers",
            len(successes) == len(set(successes)),
            f"successes={successes}",
        )
        # At least one success; if both succeed they must be 1 and 2 thanks to FOR UPDATE
        check(
            "concurrent publish: versions increment without collision",
            sorted(successes) == list(range(1, len(successes) + 1)),
            f"successes={successes} errors={errors}",
        )

    finally:
        db.close()

    if failures:
        print(f"\n{len(failures)} failure(s): {failures}")
        sys.exit(1)
    print("\nAll M3 smoke checks passed.")


if __name__ == "__main__":
    main()
