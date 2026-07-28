"""V2 draft + version tables (additive greenfield)

Revision ID: 0002_v2_draft_versions
Revises: 0001_initial
Create Date: 2026-07-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_v2_draft_versions"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

resource_type = postgresql.ENUM(
    "github",
    "figma",
    "production",
    "staging",
    "api_docs",
    "postman",
    "database_diagram",
    "drive",
    "other",
    name="resource_type",
    create_type=False,
)


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("latest_version_number", sa.Integer(), nullable=True),
    )

    op.create_table(
        "project_drafts",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("overview", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "draft_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "uploaded_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.UniqueConstraint("storage_path"),
        sa.CheckConstraint("size_bytes >= 0", name="ck_draft_files_size_bytes_non_negative"),
    )
    op.create_index("ix_draft_files_project_id", "draft_files", ["project_id"])
    op.create_index("ix_draft_files_project_created", "draft_files", ["project_id", "created_at"])

    op.create_table(
        "draft_resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("type", resource_type, nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("position >= 0", name="ck_draft_resources_position_non_negative"),
    )
    op.create_index("ix_draft_resources_project_id", "draft_resources", ["project_id"])
    op.create_index(
        "ix_draft_resources_project_position",
        "draft_resources",
        ["project_id", "position"],
    )

    op.create_table(
        "project_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("release_notes", sa.Text(), nullable=False),
        sa.Column("overview", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "published_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "project_id",
            "version_number",
            name="uq_project_versions_project_version_number",
        ),
        sa.CheckConstraint(
            "version_number >= 1",
            name="ck_project_versions_version_number_positive",
        ),
    )
    op.create_index("ix_project_versions_project_id", "project_versions", ["project_id"])
    op.create_index(
        "ix_project_versions_project_published",
        "project_versions",
        ["project_id", "published_at"],
    )

    op.create_table(
        "version_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_versions.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("storage_path"),
        sa.CheckConstraint("size_bytes >= 0", name="ck_version_files_size_bytes_non_negative"),
    )
    op.create_index("ix_version_files_version_id", "version_files", ["version_id"])

    op.create_table(
        "version_resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project_versions.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("type", resource_type, nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.CheckConstraint(
            "position >= 0",
            name="ck_version_resources_position_non_negative",
        ),
    )
    op.create_index("ix_version_resources_version_id", "version_resources", ["version_id"])
    op.create_index(
        "ix_version_resources_version_position",
        "version_resources",
        ["version_id", "position"],
    )

    # Schema integrity only — empty drafts; do not copy V1 overview/files/resources/progress.
    op.execute(
        sa.text(
            """
            INSERT INTO project_drafts (project_id, overview, updated_at)
            SELECT p.id, NULL, now()
            FROM projects p
            WHERE NOT EXISTS (
                SELECT 1 FROM project_drafts d WHERE d.project_id = p.id
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_version_resources_version_position", table_name="version_resources")
    op.drop_index("ix_version_resources_version_id", table_name="version_resources")
    op.drop_table("version_resources")

    op.drop_index("ix_version_files_version_id", table_name="version_files")
    op.drop_table("version_files")

    op.drop_index("ix_project_versions_project_published", table_name="project_versions")
    op.drop_index("ix_project_versions_project_id", table_name="project_versions")
    op.drop_table("project_versions")

    op.drop_index("ix_draft_resources_project_position", table_name="draft_resources")
    op.drop_index("ix_draft_resources_project_id", table_name="draft_resources")
    op.drop_table("draft_resources")

    op.drop_index("ix_draft_files_project_created", table_name="draft_files")
    op.drop_index("ix_draft_files_project_id", table_name="draft_files")
    op.drop_table("draft_files")

    op.drop_table("project_drafts")
    op.drop_column("projects", "latest_version_number")
