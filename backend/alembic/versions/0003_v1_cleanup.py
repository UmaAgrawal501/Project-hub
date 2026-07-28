"""Drop V1 live content tables and projects.overview

Revision ID: 0003_v1_cleanup
Revises: 0002_v2_draft_versions
Create Date: 2026-07-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_v1_cleanup"
down_revision: Union[str, None] = "0002_v2_draft_versions"
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
    op.drop_index("ix_progress_project_created", table_name="progress_entries")
    op.drop_index("ix_progress_project_id", table_name="progress_entries")
    op.drop_table("progress_entries")

    op.drop_index("ix_resources_project_position", table_name="resources")
    op.drop_index("ix_resources_project_id", table_name="resources")
    op.drop_table("resources")

    op.drop_index("ix_files_project_created", table_name="files")
    op.drop_index("ix_files_project_id", table_name="files")
    op.drop_table("files")

    op.drop_column("projects", "overview")


def downgrade() -> None:
    op.add_column("projects", sa.Column("overview", sa.Text(), nullable=True))

    op.create_table(
        "files",
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
    )
    op.create_index("ix_files_project_id", "files", ["project_id"])
    op.create_index("ix_files_project_created", "files", ["project_id", "created_at"])

    op.create_table(
        "resources",
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
    )
    op.create_index("ix_resources_project_id", "resources", ["project_id"])
    op.create_index("ix_resources_project_position", "resources", ["project_id", "position"])

    op.create_table(
        "progress_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
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
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
    )
    op.create_index("ix_progress_project_id", "progress_entries", ["project_id"])
    op.create_index(
        "ix_progress_project_created",
        "progress_entries",
        ["project_id", "created_at"],
    )
