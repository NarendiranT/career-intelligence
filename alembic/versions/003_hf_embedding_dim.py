"""switch chunk embeddings to 384-d Hugging Face MiniLM

Revision ID: 003_hf_embedding_dim
Revises: 002_user_auth
Create Date: 2026-09-05
"""

from typing import Sequence, Union

from alembic import op

revision: str = "003_hf_embedding_dim"
down_revision: Union[str, Sequence[str], None] = "002_user_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM chunks")
    op.execute("ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(384)")


def downgrade() -> None:
    op.execute("DELETE FROM chunks")
    op.execute("ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(1536)")
