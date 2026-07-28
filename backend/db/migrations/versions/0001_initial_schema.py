"""
Initial schema migration — creates all tables and extensions.

Revision ID: 0001_initial_schema
Revises: (none)
Create Date: 2026-07-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Enable pgvector extension ──────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # ── Enums ─────────────────────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE user_role AS ENUM (
                'student','working_professional','graduate','researcher','faculty'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE project_phase AS ENUM (
                'idea','validation','business','legal','patent','export'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE phase_status AS ENUM ('pending','running','completed','failed');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE document_type AS ENUM ('pdf','docx','pptx');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE member_role AS ENUM ('owner','editor','viewer');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE risk_severity AS ENUM ('low','medium','high','critical');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE forum_vote_type AS ENUM ('up','down');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "student", "working_professional", "graduate", "researcher", "faculty",
                name="user_role", create_type=False,
            ),
            nullable=False,
            server_default="student",
        ),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
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
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ── startup_categories ────────────────────────────────────────────────
    op.create_table(
        "startup_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("workflow", postgresql.JSONB, nullable=False),
        sa.Column("legal_checklist_template", postgresql.JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("name", name="uq_startup_categories_name"),
        sa.UniqueConstraint("slug", name="uq_startup_categories_slug"),
    )

    # ── projects ──────────────────────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("startup_categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("tagline", sa.String(500), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "current_phase",
            sa.Enum(
                "idea", "validation", "business", "legal", "patent", "export",
                name="project_phase", create_type=False,
            ),
            nullable=False,
            server_default="idea",
        ),
        sa.Column("ai_calls_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ai_calls_budget", sa.Integer, nullable=False, server_default="10"),
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
    op.create_index("ix_projects_user_id", "projects", ["user_id"])

    # ── project_members ───────────────────────────────────────────────────
    op.create_table(
        "project_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum("owner", "editor", "viewer", name="member_role", create_type=False),
            nullable=False,
            server_default="viewer",
        ),
        sa.Column(
            "invited_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_members_project_id_user_id"),
    )
    op.create_index("ix_project_members_project_id", "project_members", ["project_id"])

    # ── project_memory ────────────────────────────────────────────────────
    op.create_table(
        "project_memory",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key", sa.String(200), nullable=False),
        sa.Column("value", postgresql.JSONB, nullable=False),
        # 384-dim vector — stored as text if pgvector not installed
        sa.Column("embedding", sa.Text, nullable=True),
        sa.Column("source_phase", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("project_id", "key", name="uq_project_memory_project_id_key"),
    )
    op.create_index("ix_project_memory_project_id", "project_memory", ["project_id"])
    op.create_index("ix_project_memory_key", "project_memory", ["key"])

    # Alter embedding column to vector(384) after pgvector is confirmed
    op.execute("ALTER TABLE project_memory ALTER COLUMN embedding TYPE vector(384) USING NULL::vector(384);")

    # ── idea_analysis ─────────────────────────────────────────────────────
    op.create_table(
        "idea_analysis",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("problem_statement", sa.Text, nullable=True),
        sa.Column("target_audience", sa.Text, nullable=True),
        sa.Column("value_proposition", sa.Text, nullable=True),
        sa.Column("category_detection", postgresql.JSONB, nullable=True),
        sa.Column("category_confidence", sa.Float, nullable=True),
        sa.Column("raw_output", postgresql.JSONB, nullable=True),
        sa.Column("user_edited", sa.Boolean, nullable=False, server_default="false"),
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
    op.create_index("ix_idea_analysis_project_id", "idea_analysis", ["project_id"])

    # ── validation_reports ────────────────────────────────────────────────
    op.create_table(
        "validation_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("market_summary", sa.Text, nullable=True),
        sa.Column("competitor_summary", sa.Text, nullable=True),
        sa.Column("swot", postgresql.JSONB, nullable=True),
        sa.Column("score_breakdown", postgresql.JSONB, nullable=True),
        sa.Column("total_score", sa.Float, nullable=True),
        sa.Column("citations", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_validation_reports_project_id", "validation_reports", ["project_id"])

    # ── scores ────────────────────────────────────────────────────────────
    op.create_table(
        "scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "validation_report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("validation_reports.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("dimension", sa.String(50), nullable=False),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("weight", sa.Float, nullable=False),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("value >= 0 AND value <= 100", name="ck_scores_value_range"),
    )
    op.create_index("ix_scores_project_id", "scores", ["project_id"])

    # ── risk_assessments ──────────────────────────────────────────────────
    op.create_table(
        "risk_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("risk_type", sa.String(100), nullable=False),
        sa.Column(
            "severity",
            sa.Enum(
                "low", "medium", "high", "critical",
                name="risk_severity", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("mitigation", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_risk_assessments_project_id", "risk_assessments", ["project_id"])

    # ── business_plans ────────────────────────────────────────────────────
    op.create_table(
        "business_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("lean_canvas", postgresql.JSONB, nullable=False),
        sa.Column("revenue_model", sa.Text, nullable=True),
        sa.Column("pricing_notes", sa.Text, nullable=True),
        sa.Column("user_edited", sa.Boolean, nullable=False, server_default="false"),
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
    op.create_index("ix_business_plans_project_id", "business_plans", ["project_id"])

    # ── legal_checklists ──────────────────────────────────────────────────
    op.create_table(
        "legal_checklists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("checklist_items", postgresql.JSONB, nullable=False),
        sa.Column("completed_items", postgresql.JSONB, nullable=False, server_default="'{}'"),
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
    op.create_index("ix_legal_checklists_project_id", "legal_checklists", ["project_id"])

    # ── legal_documents ───────────────────────────────────────────────────
    op.create_table(
        "legal_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("document_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("storage_url", sa.String(500), nullable=True),
        sa.Column("user_edited", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_legal_documents_project_id", "legal_documents", ["project_id"])

    # ── patent_research_reports ───────────────────────────────────────────
    op.create_table(
        "patent_research_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("query_used", sa.Text, nullable=True),
        sa.Column("results", postgresql.JSONB, nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("user_pdf_url", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_patent_research_reports_project_id", "patent_research_reports", ["project_id"])

    # ── documents ─────────────────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "doc_type",
            sa.Enum("pdf", "docx", "pptx", name="document_type", create_type=False),
            nullable=False,
        ),
        sa.Column("phase", sa.String(50), nullable=True),
        sa.Column("filename", sa.String(300), nullable=False),
        sa.Column("storage_url", sa.String(500), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_documents_project_id", "documents", ["project_id"])

    # ── phase_log ─────────────────────────────────────────────────────────
    op.create_table(
        "phase_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("phase", sa.String(50), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "running", "completed", "failed",
                name="phase_status", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("task_id", sa.String(200), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_phase_log_project_id", "phase_log", ["project_id"])

    # ── forum_posts ───────────────────────────────────────────────────────
    op.create_table(
        "forum_posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        sa.Column("upvotes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("downvotes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_pinned", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
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
    op.create_index("ix_forum_posts_author_id", "forum_posts", ["author_id"])

    # ── forum_comments ────────────────────────────────────────────────────
    op.create_table(
        "forum_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("forum_posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("forum_comments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("upvotes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_forum_comments_post_id", "forum_comments", ["post_id"])

    # ── forum_votes ───────────────────────────────────────────────────────
    op.create_table(
        "forum_votes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("forum_posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vote_type",
            sa.Enum("up", "down", name="forum_vote_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("post_id", "user_id", name="uq_forum_votes_post_id_user_id"),
    )
    op.create_index("ix_forum_votes_post_id", "forum_votes", ["post_id"])


def downgrade() -> None:
    # Drop in reverse FK order
    op.drop_table("forum_votes")
    op.drop_table("forum_comments")
    op.drop_table("forum_posts")
    op.drop_table("phase_log")
    op.drop_table("documents")
    op.drop_table("patent_research_reports")
    op.drop_table("legal_documents")
    op.drop_table("legal_checklists")
    op.drop_table("business_plans")
    op.drop_table("risk_assessments")
    op.drop_table("scores")
    op.drop_table("validation_reports")
    op.drop_table("idea_analysis")
    op.drop_table("project_memory")
    op.drop_table("project_members")
    op.drop_table("projects")
    op.drop_table("startup_categories")
    op.drop_table("users")

    # Drop enums
    for enum_name in [
        "forum_vote_type", "risk_severity", "member_role",
        "document_type", "phase_status", "project_phase", "user_role",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name};")

    op.execute("DROP EXTENSION IF EXISTS vector;")
