"""Version-locked project shares (one token per published version)

Revision ID: 0004_version_locked_shares
Revises: 0003_v1_cleanup
Create Date: 2026-07-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_version_locked_shares"
down_revision: Union[str, None] = "0003_v1_cleanup"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "project_shares",
        sa.Column("version_number", sa.Integer(), nullable=True),
    )

    op.execute(
        """
        UPDATE project_shares AS s
        SET version_number = p.latest_version_number
        FROM projects AS p
        WHERE s.project_id = p.id
          AND p.latest_version_number IS NOT NULL
        """
    )

    # Shares without a published version cannot be version-locked — remove them.
    op.execute(
        """
        DELETE FROM project_shares
        WHERE version_number IS NULL
        """
    )

    op.alter_column(
        "project_shares",
        "version_number",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.drop_constraint("uq_project_shares_project_id", "project_shares", type_="unique")
    op.create_unique_constraint(
        "uq_project_shares_project_version",
        "project_shares",
        ["project_id", "version_number"],
    )
    op.create_index(
        "ix_project_shares_project_id",
        "project_shares",
        ["project_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_project_shares_project_id", table_name="project_shares")
    op.drop_constraint(
        "uq_project_shares_project_version",
        "project_shares",
        type_="unique",
    )

    # Keep only the highest version_number share per project before restoring uniqueness.
    op.execute(
        """
        DELETE FROM project_shares AS s
        WHERE EXISTS (
            SELECT 1
            FROM project_shares AS other
            WHERE other.project_id = s.project_id
              AND other.version_number > s.version_number
        )
        """
    )

    op.create_unique_constraint(
        "uq_project_shares_project_id",
        "project_shares",
        ["project_id"],
    )
    op.drop_column("project_shares", "version_number")
