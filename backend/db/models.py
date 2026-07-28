"""
SQLAlchemy ORM models — one class per Supabase table.

Design decisions:
- UUIDs everywhere as primary keys (gen_random_uuid() default in Postgres).
- pgvector column on project_memory for semantic search.
- JSONB columns for flexible structured data (SWOT, score_breakdown, etc.).
- All timestamps use TIMESTAMPTZ (UTC stored, any tz displayable).
- Row Level Security is enforced at the Postgres level; the application
  layer still checks ownership before mutating records.

Import order matters for FK resolution — keep models in dependency order.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base

# ── Custom pgvector type ──────────────────────────────────────────────────────
# We use a raw String column holding the vector literal until pgvector's
# SQLAlchemy integration is pinned.  Swap for Vector(384) once pgvector-python
# is added to pyproject.toml.
try:
    from pgvector.sqlalchemy import Vector  # type: ignore

    VECTOR_TYPE = Vector(384)
except ImportError:  # pgvector not installed — fall back to text storage
    VECTOR_TYPE = Text  # type: ignore

# ── Enums ─────────────────────────────────────────────────────────────────────
UserRoleEnum = Enum(
    "student",
    "working_professional",
    "graduate",
    "researcher",
    "faculty",
    name="user_role",
)

ProjectPhaseEnum = Enum(
    "idea",
    "validation",
    "business",
    "legal",
    "patent",
    "export",
    name="project_phase",
)

PhaseStatusEnum = Enum(
    "pending",
    "running",
    "completed",
    "failed",
    name="phase_status",
)

DocumentTypeEnum = Enum(
    "pdf",
    "docx",
    "pptx",
    name="document_type",
)

ForumVoteTypeEnum = Enum("up", "down", name="forum_vote_type")


# ── Models ────────────────────────────────────────────────────────────────────


class User(Base):
    """
    Application user — mirrors Supabase Auth users.

    We keep a shadow record here so we can attach application-level metadata
    (role, bio) without touching Supabase Auth's `auth.users` table directly.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Must match the Supabase Auth user UUID",
    )
    email: Mapped[str] = mapped_column(
        String(320), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(
        UserRoleEnum,
        nullable=False,
        default="student",
        server_default="student",
    )
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    memberships: Mapped[list["ProjectMember"]] = relationship(back_populates="user")
    forum_posts: Mapped[list["ForumPost"]] = relationship(back_populates="author")


class StartupCategory(Base):
    """
    System-defined startup categories with their workflow JSON.

    The `workflow` column holds an ordered list of phase names that define
    the progression for that category type (e.g. SaaS may skip patent phase).

    Seeded by: db/seeds/categories.py
    """

    __tablename__ = "startup_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array of phase names in order, e.g. ["idea","validation","business","legal"]
    workflow: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    # Legal checklist template (static JSON)
    legal_checklist_template: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    projects: Mapped[list["Project"]] = relationship(back_populates="category")


class Project(Base):
    """
    Core entity — one startup idea owned by a user.

    `current_phase` is updated by the Workflow Engine each time a phase
    completes.  The FK to startup_categories is nullable so a user can
    start without picking a category (the idea crew auto-detects it).
    """

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("startup_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    tagline: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_phase: Mapped[str] = mapped_column(
        ProjectPhaseEnum, nullable=False, default="idea", server_default="idea"
    )
    # AI call budget tracking (reset per run)
    ai_calls_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ai_calls_budget: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="projects")
    category: Mapped["StartupCategory | None"] = relationship(back_populates="projects")
    members: Mapped[list["ProjectMember"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    memory: Mapped[list["ProjectMemory"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    idea_analysis: Mapped["IdeaAnalysis | None"] = relationship(
        back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    validation_reports: Mapped[list["ValidationReport"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    scores: Mapped[list["Score"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    risk_assessments: Mapped[list["RiskAssessment"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    business_plans: Mapped[list["BusinessPlan"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    legal_checklists: Mapped[list["LegalChecklist"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    legal_documents: Mapped[list["LegalDocument"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    patent_reports: Mapped[list["PatentResearchReport"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    phase_logs: Mapped[list["PhaseLog"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    forum_posts: Mapped[list["ForumPost"]] = relationship(back_populates="project")


class ProjectMember(Base):
    """
    Many-to-many between users and projects with a role column.

    Roles: owner | editor | viewer
    The project owner is always implicitly an owner-level member; the explicit
    row is created by the invite flow.
    """

    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        Enum("owner", "editor", "viewer", name="member_role"),
        nullable=False,
        default="viewer",
    )
    invited_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(
        back_populates="memberships", foreign_keys=[user_id]
    )


class ProjectMemory(Base):
    """
    Cross-phase shared memory for a project.

    This is the MOST IMPORTANT table — every AI phase reads relevant rows
    before generation and writes new rows after.  The `embedding` column
    (pgvector) enables semantic similarity retrieval so the LLM context
    stays relevant rather than loading everything.

    Key examples:
        key="idea_problem_statement", source_phase="idea"
        key="competitor_summary",     source_phase="validation"
        key="swot",                   source_phase="validation"
    """

    __tablename__ = "project_memory"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    # 384-dim embedding from sentence-transformers/all-MiniLM-L6-v2
    embedding: Mapped[str | None] = mapped_column(VECTOR_TYPE, nullable=True)
    source_phase: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("project_id", "key"),)

    project: Mapped["Project"] = relationship(back_populates="memory")


class IdeaAnalysis(Base):
    """
    Structured output from the Idea Analysis phase (M3).

    One row per project — replaced if re-run.
    """

    __tablename__ = "idea_analysis"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    problem_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_proposition: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Structured JSON from LLM: {category, confidence, reasoning}
    category_detection: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    category_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Full structured output blob for reference / re-display
    raw_output: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    # Was this output edited by the user before saving?
    user_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project: Mapped["Project"] = relationship(back_populates="idea_analysis")


class ValidationReport(Base):
    """
    Market research, competitor analysis, SWOT, and readiness score.

    Multiple reports allowed per project (user can re-run).  The latest
    is considered current.
    """

    __tablename__ = "validation_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    market_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    competitor_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # {strengths: [], weaknesses: [], opportunities: [], threats: []}
    swot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    # {validation: n, business: n, market: n, ...} — LLM sub-scores (inputs)
    score_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    # Deterministic weighted sum computed in Python (see scoring.py)
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Search result citations for transparency
    citations: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="validation_reports")
    scores: Mapped[list["Score"]] = relationship(
        back_populates="validation_report", cascade="all, delete-orphan"
    )


class Score(Base):
    """
    One row per scoring dimension per validation run.

    Dimensions: validation, business, market, technology, patent,
                financial, legal, overall

    The `value` is the LLM-provided sub-rating (0–100 normalized).
    The `weight` and weighted sum are computed in Python.
    """

    __tablename__ = "scores"
    __table_args__ = (
        CheckConstraint("value >= 0 AND value <= 100", name="ck_scores_value_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    validation_report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("validation_reports.id", ondelete="CASCADE"),
        nullable=True,
    )
    dimension: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="scores")
    validation_report: Mapped["ValidationReport | None"] = relationship(
        back_populates="scores"
    )


class RiskAssessment(Base):
    """
    Structured risk items output by the validation/risk crew.

    One row per risk item (multiple per project run).
    """

    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    risk_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", "critical", name="risk_severity"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    mitigation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="risk_assessments")


class BusinessPlan(Base):
    """
    Lean Canvas / BMC generated from project_memory.

    The `lean_canvas` JSONB contains all 9 canvas blocks.
    """

    __tablename__ = "business_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # {problem, solution, unique_value_prop, unfair_advantage,
    #  customer_segments, key_metrics, channels, revenue_streams, cost_structure}
    lean_canvas: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    revenue_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    pricing_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project: Mapped["Project"] = relationship(back_populates="business_plans")


class LegalChecklist(Base):
    """
    Static legal / registration checklist for a project.

    Content is loaded from static JSON templates (not LLM-generated).
    The `completed_items` JSONB tracks which items the user has checked off.

    ⚠️  GUARDRAIL: This table stores static compliance information only.
         Always display: "Last verified: [date] — consult a professional."
    """

    __tablename__ = "legal_checklists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    # [{id, title, description, required, url, last_verified}, ...]
    checklist_items: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    # {item_id: true/false}
    completed_items: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default={}
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project: Mapped["Project"] = relationship(back_populates="legal_checklists")


class LegalDocument(Base):
    """
    AI-drafted legal document (NDA, Founder Agreement, etc.).

    ⚠️  GUARDRAIL: Header and footer MUST display
        "AI-generated draft — have a qualified lawyer review before use."
    """

    __tablename__ = "legal_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Supabase Storage URL for the generated PDF
    storage_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="legal_documents")


class PatentResearchReport(Base):
    """
    Output from the patent/prior-art research crew.

    Sources: PatentsView (US), Tavily/Exa web search (global),
             optional user-uploaded PDF comparison.
    """

    __tablename__ = "patent_research_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    query_used: Mapped[str | None] = mapped_column(Text, nullable=True)
    # [{patent_id, title, abstract, similarity_score, source}, ...]
    results: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Path to user-uploaded comparison PDF in Supabase Storage
    user_pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="patent_reports")


class Document(Base):
    """
    Generated export files (PDF, DOCX, PPTX) stored in Supabase Storage.
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    doc_type: Mapped[str] = mapped_column(DocumentTypeEnum, nullable=False)
    phase: Mapped[str | None] = mapped_column(String(50), nullable=True)
    filename: Mapped[str] = mapped_column(String(300), nullable=False)
    storage_url: Mapped[str] = mapped_column(String(500), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="documents")


class PhaseLog(Base):
    """
    Audit log of phase transitions and their status.

    The Workflow Engine writes here whenever a phase starts, completes,
    or fails.  The frontend polls this to show progress.
    """

    __tablename__ = "phase_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phase: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(PhaseStatusEnum, nullable=False)
    task_id: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="arq/Celery task ID for polling"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    project: Mapped["Project"] = relationship(back_populates="phase_logs")


class ForumPost(Base):
    """
    Community forum post — can optionally be linked to a project.
    """

    __tablename__ = "forum_posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    upvotes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    downvotes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    author: Mapped["User"] = relationship(back_populates="forum_posts")
    project: Mapped["Project | None"] = relationship(back_populates="forum_posts")
    comments: Mapped[list["ForumComment"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    votes: Mapped[list["ForumVote"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class ForumComment(Base):
    """Reply to a forum post — supports one level of nesting via parent_id."""

    __tablename__ = "forum_comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forum_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forum_comments.id", ondelete="SET NULL"),
        nullable=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    upvotes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    post: Mapped["ForumPost"] = relationship(back_populates="comments")


class ForumVote(Base):
    """
    One vote per user per post — enforced by unique constraint.
    Upvote/downvote toggling is handled in the service layer.
    """

    __tablename__ = "forum_votes"
    __table_args__ = (UniqueConstraint("post_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forum_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    vote_type: Mapped[str] = mapped_column(ForumVoteTypeEnum, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    post: Mapped["ForumPost"] = relationship(back_populates="votes")
