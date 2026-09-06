"""add interview topics and conversation kind

Revision ID: 005_interview_topics
Revises: 004_conversation_bookmarks
Create Date: 2026-09-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_interview_topics"
down_revision: Union[str, Sequence[str], None] = "004_conversation_bookmarks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conversation_kind = postgresql.ENUM("assistant", "interview", name="conversation_kind")
    conversation_kind.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("label", sa.String(256), nullable=False),
        sa.Column("slug", sa.String(256), nullable=False),
        sa.Column(
            "source_conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("context", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_topics_user_id", "topics", ["user_id"])
    op.create_unique_constraint("uq_topics_user_slug", "topics", ["user_id", "slug"])

    op.add_column(
        "conversations",
        sa.Column(
            "kind",
            postgresql.ENUM("assistant", "interview", name="conversation_kind", create_type=False),
            nullable=False,
            server_default="assistant",
        ),
    )
    op.add_column(
        "conversations",
        sa.Column(
            "topic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("topics.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index("ix_conversations_kind", "conversations", ["kind"])
    op.create_index("ix_conversations_topic_id", "conversations", ["topic_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_conversations_topic_id", table_name="conversations")
    op.drop_index("ix_conversations_kind", table_name="conversations")
    op.drop_column("conversations", "topic_id")
    op.drop_column("conversations", "kind")
    op.drop_constraint("uq_topics_user_slug", "topics", type_="unique")
    op.drop_index("ix_topics_user_id", table_name="topics")
    op.drop_table("topics")
    postgresql.ENUM(name="conversation_kind").drop(op.get_bind(), checkfirst=True)
