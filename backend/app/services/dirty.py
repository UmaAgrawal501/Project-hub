"""Dirty / unpublished-changes helpers (V2)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Project, ProjectVersion
from app.repositories.draft_repository import (
    DraftFileRepository,
    DraftRepository,
    DraftResourceRepository,
)
from app.repositories.version_repository import VersionRepository


def has_unpublished_changes(project: Project, db: Session | None = None) -> bool:
    """
    Normative:
    - latest_version_number is null → False (never published is not dirty)
    - else compare live name + draft content to that Version snapshot
    """
    if project.latest_version_number is None:
        return False
    if db is None:
        # Call sites that only have the project and no session should not claim dirty.
        return False

    version = VersionRepository(db).get_by_number(
        project_id=project.id,
        version_number=project.latest_version_number,
    )
    if version is None:
        return True

    return _draft_differs_from_version(db=db, project=project, version=version)


def _draft_differs_from_version(
    *,
    db: Session,
    project: Project,
    version: ProjectVersion,
) -> bool:
    if project.name != version.name:
        return True

    draft = DraftRepository(db).get_or_create(project_id=project.id)
    draft_overview = draft.overview
    version_overview = version.overview
    if (draft_overview or None) != (version_overview or None):
        return True

    draft_files = DraftFileRepository(db).list_for_project(project_id=project.id)
    version_files = VersionRepository(db).list_files(version_id=version.id)
    file_sig = lambda rows: sorted(
        (r.name, r.mime_type, int(r.size_bytes)) for r in rows
    )
    if file_sig(draft_files) != file_sig(version_files):
        return True

    draft_resources = DraftResourceRepository(db).list_for_project(project_id=project.id)
    version_resources = VersionRepository(db).list_resources(version_id=version.id)
    res_sig = lambda rows: sorted(
        (
            r.title,
            r.url,
            r.type.value if hasattr(r.type, "value") else str(r.type),
            r.description or None,
            int(r.position),
        )
        for r in rows
    )
    if res_sig(draft_resources) != res_sig(version_resources):
        return True

    return False
