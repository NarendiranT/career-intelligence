"""add conversation bookmark fields

Revision ID: 004_conversation_bookmarks
Revises: 003_hf_embedding_dim
Create Date: 2026-09-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_conversation_bookmarks"
down_revision: Union[str, Sequence[str], None] = "003_hf_embedding_dim"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("bookmarked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "conversations",
        sa.Column("bookmarked_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversations", "bookmarked_at")
    op.drop_column("conversations", "bookmarked")
