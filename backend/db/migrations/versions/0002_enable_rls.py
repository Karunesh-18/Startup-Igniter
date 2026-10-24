"""Enable row-level security on every public table.

Supabase exposes the public schema over PostgREST to the publishable key.
With RLS on and no policies, that key sees nothing; the backend connects as
the postgres role (bypasses RLS) and enforces ownership itself.

Revision ID: 0002_enable_rls
Revises: 0001_initial_schema
"""

from alembic import op

revision = "0002_enable_rls"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

_DO = """
DO $$ DECLARE t text; BEGIN
  FOR t IN SELECT tablename FROM pg_tables
           WHERE schemaname = 'public' AND tablename <> 'alembic_version'
  LOOP EXECUTE format('ALTER TABLE public.%I {action} ROW LEVEL SECURITY', t); END LOOP;
END $$;
"""


def upgrade() -> None:
    op.execute(_DO.format(action="ENABLE"))
    op.execute("ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute(_DO.format(action="DISABLE"))
    op.execute("ALTER TABLE public.alembic_version DISABLE ROW LEVEL SECURITY")
