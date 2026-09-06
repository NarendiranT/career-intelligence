from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship as sa_relationship
from sqlmodel import Field, Relationship, SQLModel

from backend.config import settings


class DocType(StrEnum):
    resume = "resume"
    job = "job"


class DocumentStatus(StrEnum):
    uploaded = "uploaded"
    processing = "processing"
    processed = "processed"
    failed = "failed"


class MessageRole(StrEnum):
    user = "user"
    assistant = "assistant"


class ConversationKind(StrEnum):
    assistant = "assistant"
    interview = "interview"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
    )
    email: str = Field(
        max_length=320,
        sa_column=Column(String(320), unique=True, index=True, nullable=False),
    )
    full_name: str = Field(default="", max_length=256)
    password_hash: str | None = Field(default=None, max_length=255)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    )
    doc_type: DocType | None = Field(default=None, sa_column=Column(Enum(DocType, name="doc_type"), nullable=True))
    filename: str = Field(max_length=512)
    storage_path: str = Field(max_length=1024)
    status: DocumentStatus = Field(
        default=DocumentStatus.uploaded,
        sa_column=Column(Enum(DocumentStatus, name="document_status"), nullable=False),
    )
    mime: str | None = Field(default=None, max_length=128)
    size: int | None = None
    error_message: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )

    user: User | None = Relationship(sa_relationship=sa_relationship("User"))
    chunks: list[Chunk] = Relationship(
        back_populates="document",
        sa_relationship=sa_relationship(
            "Chunk",
            back_populates="document",
            cascade="all, delete-orphan",
        ),
    )
    resume_profile: ResumeProfile | None = Relationship(
        back_populates="document",
        sa_relationship=sa_relationship(
            "ResumeProfile",
            back_populates="document",
            cascade="all, delete-orphan",
        ),
    )
    job_profile: JobProfile | None = Relationship(
        back_populates="document",
        sa_relationship=sa_relationship(
            "JobProfile",
            back_populates="document",
            cascade="all, delete-orphan",
        ),
    )


class ResumeProfile(SQLModel, table=True):
    __tablename__ = "resume_profiles"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
    )
    document_id: uuid.UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("documents.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        )
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    )
    name: str | None = Field(default=None, max_length=256)
    headline: str | None = Field(default=None, max_length=512)
    skills: list[Any] = Field(default_factory=list, sa_column=Column(JSONB, nullable=True))
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB, nullable=True))

    document: Document | None = Relationship(
        back_populates="resume_profile",
        sa_relationship=sa_relationship("Document", back_populates="resume_profile"),
    )


class JobProfile(SQLModel, table=True):
    __tablename__ = "job_profiles"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
    )
    document_id: uuid.UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("documents.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        )
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    )
    title: str | None = Field(default=None, max_length=256)
    company: str | None = Field(default=None, max_length=256)
    skills: list[Any] = Field(default_factory=list, sa_column=Column(JSONB, nullable=True))
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB, nullable=True))

    document: Document | None = Relationship(
        back_populates="job_profile",
        sa_relationship=sa_relationship("Document", back_populates="job_profile"),
    )


class Chunk(SQLModel, table=True):
    __tablename__ = "chunks"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
    )
    document_id: uuid.UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    )
    content: str = Field(sa_column=Column(Text, nullable=False))
    embedding: list[float] = Field(sa_column=Column(Vector(settings.embedding_dim), nullable=False))
    chunk_metadata: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column("metadata", JSONB, nullable=True),
    )
    ordinal: int = Field(default=0)

    document: Document | None = Relationship(
        back_populates="chunks",
        sa_relationship=sa_relationship("Document", back_populates="chunks"),
    )


class Topic(SQLModel, table=True):
    __tablename__ = "topics"
    __table_args__ = (UniqueConstraint("user_id", "slug", name="uq_topics_user_slug"),)

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    )
    label: str = Field(max_length=256)
    slug: str = Field(max_length=256)
    source_conversation_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("conversations.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    source_message_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(PGUUID(as_uuid=True), nullable=True),
    )
    context: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    user: User | None = Relationship(sa_relationship=sa_relationship("User"))


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    bookmarked: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default="false"),
    )
    bookmarked_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    kind: ConversationKind = Field(
        default=ConversationKind.assistant,
        sa_column=Column(
            Enum(ConversationKind, name="conversation_kind"),
            nullable=False,
            server_default="assistant",
        ),
    )
    topic_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("topics.id", ondelete="CASCADE"),
            nullable=True,
            unique=True,
        ),
    )

    user: User | None = Relationship(sa_relationship=sa_relationship("User"))
    messages: list[Message] = Relationship(
        back_populates="conversation",
        sa_relationship=sa_relationship(
            "Message",
            back_populates="conversation",
            cascade="all, delete-orphan",
        ),
    )


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
    )
    conversation_id: uuid.UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    user_id: uuid.UUID = Field(sa_column=Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False))
    role: MessageRole = Field(sa_column=Column(Enum(MessageRole, name="message_role"), nullable=False))
    content: str = Field(sa_column=Column(Text, nullable=False))
    citations: list[Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    extra: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    conversation: Conversation | None = Relationship(
        back_populates="messages",
        sa_relationship=sa_relationship("Conversation", back_populates="messages"),
    )


class UsageEvent(SQLModel, table=True):
    __tablename__ = "usage_events"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    )
    conversation_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("conversations.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    event_type: str = Field(max_length=64)
    model: str | None = Field(default=None, max_length=128)
    tokens: int | None = None
    latency_ms: float | None = Field(default=None, sa_column=Column(Float, nullable=True))
    extra: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
