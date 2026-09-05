"""user credentials for JWT auth

Revision ID: 002_user_auth
Revises: 001_initial
Create Date: 2026-09-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_user_auth"
down_revision: Union[str, Sequence[str], None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("full_name", sa.String(256), nullable=True, server_default=""))
    op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))
    op.execute(
        """
        UPDATE users
        SET email = 'legacy-' || id::text || '@local.invalid'
        WHERE email IS NULL OR btrim(email) = ''
        """
    )
    op.execute(
        """
        WITH ranked AS (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY lower(email) ORDER BY created_at, id) AS rn
            FROM users
        )
        UPDATE users AS u
        SET email = u.email || '+' || u.id::text
        FROM ranked AS r
        WHERE u.id = r.id AND r.rn > 1
        """
    )
    op.alter_column("users", "email", existing_type=sa.String(320), nullable=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.alter_column("users", "full_name", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.alter_column("users", "email", existing_type=sa.String(320), nullable=True)
    op.drop_column("users", "password_hash")
    op.drop_column("users", "full_name")
