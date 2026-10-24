"""Product tables: saved ideas, analysis runs, chat, experiments, billing, integrations.

Keyed by the Supabase auth user id (`owner_id`); no dependency on the legacy
`users`/`projects` tables. Portable types so the same models run on Postgres
(prod) and SQLite (tests).
"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base

JSON = sa.JSON().with_variant(JSONB, "postgresql")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)


def _ts(**kw) -> Mapped[datetime]:
    return mapped_column(sa.DateTime(timezone=True), default=_now, **kw)


class Idea(Base):
    """A founder's idea. Each re-analysis is a new Analysis version under it."""

    __tablename__ = "ideas"

    id: Mapped[uuid.UUID] = _uuid_pk()
    owner_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, index=True)
    title: Mapped[str] = mapped_column(sa.String(200))
    idea_text: Mapped[str] = mapped_column(sa.Text)
    archived: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    github_repo: Mapped[str | None] = mapped_column(sa.String(200), nullable=True)
    created_at: Mapped[datetime] = _ts()
    updated_at: Mapped[datetime] = _ts(onupdate=_now)


class Analysis(Base):
    """One full pipeline run for an idea version."""

    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = _uuid_pk()
    idea_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("ideas.id", ondelete="CASCADE"), index=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, index=True)
    version: Mapped[int] = mapped_column(sa.Integer, default=1)
    idea_text: Mapped[str] = mapped_column(sa.Text)
    status: Mapped[str] = mapped_column(sa.String(20), default="running")  # running|complete|failed|cancelled
    mode: Mapped[str] = mapped_column(sa.String(10), default="live")  # live|mock
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    overall_score: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    verdict: Mapped[str | None] = mapped_column(sa.String(20), nullable=True)  # go|pivot|no-go
    grounding_score: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    unlocked: Mapped[bool] = mapped_column(sa.Boolean, default=False)  # full report paid for / Pro
    error: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = _ts()
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = _uuid_pk()
    idea_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("ideas.id", ondelete="CASCADE"), index=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, index=True)
    role: Mapped[str] = mapped_column(sa.String(12))  # user|assistant
    content: Mapped[str] = mapped_column(sa.Text)
    # {"title","idea_text","changes":[{field,from,to}]} when the assistant proposes an edit
    proposal: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    proposal_status: Mapped[str | None] = mapped_column(sa.String(12), nullable=True)  # pending|accepted|dismissed
    created_at: Mapped[datetime] = _ts()


class Experiment(Base):
    """A testable hypothesis taken from the report, tracked over time."""

    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = _uuid_pk()
    idea_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("ideas.id", ondelete="CASCADE"), index=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, index=True)
    hypothesis: Mapped[str] = mapped_column(sa.Text)
    metric: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    status: Mapped[str] = mapped_column(sa.String(16), default="open")  # open|running|validated|invalidated
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = _ts()
    updated_at: Mapped[datetime] = _ts(onupdate=_now)


class Payment(Base):
    """A Razorpay order (one-time report unlock) or subscription charge. Amounts in paise (INR)."""

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = _uuid_pk()
    owner_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, index=True)
    kind: Mapped[str] = mapped_column(sa.String(12))  # report|pro
    analysis_id: Mapped[uuid.UUID | None] = mapped_column(sa.Uuid, nullable=True)
    amount_paise: Mapped[int] = mapped_column(sa.Integer)
    currency: Mapped[str] = mapped_column(sa.String(3), default="INR")
    razorpay_order_id: Mapped[str | None] = mapped_column(sa.String(64), unique=True, nullable=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(sa.String(64), unique=True, nullable=True)
    status: Mapped[str] = mapped_column(sa.String(12), default="created")  # created|paid|failed
    created_at: Mapped[datetime] = _ts()
    paid_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)


class Subscription(Base):
    __tablename__ = "subscriptions"

    owner_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True)
    plan: Mapped[str] = mapped_column(sa.String(12), default="pro")
    status: Mapped[str] = mapped_column(sa.String(16), default="created")  # created|active|cancelled|halted
    razorpay_subscription_id: Mapped[str | None] = mapped_column(sa.String(64), unique=True, nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = _ts(onupdate=_now)


class WebhookEvent(Base):
    """Processed webhook ids, for idempotent handling."""

    __tablename__ = "webhook_events"

    id: Mapped[str] = mapped_column(sa.String(80), primary_key=True)
    received_at: Mapped[datetime] = _ts()


class Integration(Base):
    """A connected third-party account. `secret` is Fernet-encrypted."""

    __tablename__ = "integrations"
    __table_args__ = (sa.UniqueConstraint("owner_id", "provider"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    owner_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, index=True)
    provider: Mapped[str] = mapped_column(sa.String(24))  # github|slack|notion|webhook
    label: Mapped[str | None] = mapped_column(sa.String(120), nullable=True)
    secret: Mapped[str] = mapped_column(sa.Text)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = _ts()
