"""Product tables: ideas, analyses, chat, experiments, billing, integrations (RLS on).

Revision ID: 0003_product_tables
Revises: 0002_enable_rls
"""

from alembic import op

from db import product

revision = "0003_product_tables"
down_revision = "0002_enable_rls"
branch_labels = None
depends_on = None

_TABLES = [
    product.Idea, product.Analysis, product.ChatMessage, product.Experiment,
    product.Payment, product.Subscription, product.WebhookEvent, product.Integration,
]


def upgrade() -> None:
    # Created from the models so Postgres (JSONB) and tests (JSON) stay in lockstep.
    # Later schema changes must be their own migrations.
    bind = op.get_bind()
    for model in _TABLES:
        model.__table__.create(bind, checkfirst=True)
        op.execute(f'ALTER TABLE public."{model.__tablename__}" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    bind = op.get_bind()
    for model in reversed(_TABLES):
        model.__table__.drop(bind, checkfirst=True)
