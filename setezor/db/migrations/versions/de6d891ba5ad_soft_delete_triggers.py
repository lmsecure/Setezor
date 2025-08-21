"""soft_delete_triggers

Revision ID: de6d891ba5ad
Revises: 5601b441367a
Create Date: 2025-08-12 09:50:59.139706

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = 'de6d891ba5ad'
down_revision: Union[str, None] = '5601b441367a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.execute(f"""
        CREATE OR REPLACE FUNCTION soft_delete_project_cascade()
        RETURNS trigger AS $$
        DECLARE
          child RECORD;
          sql TEXT;
          parent_table_name TEXT := TG_TABLE_NAME;
        BEGIN
          IF NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL THEN
            FOR child IN
              EXECUTE format($f$
                SELECT
                  child_ns.nspname AS child_schema,
                  child.relname AS child_table,
                  child_col.attname AS child_column
                FROM
                  pg_constraint con
                  JOIN pg_class parent ON con.confrelid = parent.oid
                  JOIN pg_namespace parent_ns ON parent.relnamespace = parent_ns.oid
                  JOIN pg_class child ON con.conrelid = child.oid
                  JOIN pg_namespace child_ns ON child.relnamespace = child_ns.oid
                  JOIN unnest(con.conkey) WITH ORDINALITY AS child_cols(colid, ord) ON TRUE
                  JOIN unnest(con.confkey) WITH ORDINALITY AS parent_cols(colid, ord) ON child_cols.ord = parent_cols.ord
                  JOIN pg_attribute child_col ON (child_col.attrelid = child.oid AND child_col.attnum = child_cols.colid)
                WHERE
                  con.contype = 'f'
                  AND parent.relname = %L
              $f$, parent_table_name)
            LOOP
              PERFORM 1 FROM information_schema.columns
               WHERE table_schema = child.child_schema
                 AND table_name = child.child_table
                 AND column_name = 'deleted_at';
        
              IF FOUND THEN
                sql := format(
                  'UPDATE %I.%I SET deleted_at = NOW() WHERE %I = $1 AND deleted_at IS NULL',
                  child.child_schema,
                  child.child_table,
                  child.child_column
                );
                EXECUTE sql USING NEW.id;
              END IF;
            END LOOP;
          END IF;
        
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute(f"""
        CREATE TRIGGER trg_soft_delete_project_cascade
        BEFORE UPDATE ON project
        FOR EACH ROW
        WHEN (OLD.deleted_at IS NULL AND NEW.deleted_at IS NOT NULL)
        EXECUTE FUNCTION soft_delete_project_cascade();
    """)


def downgrade() -> None:
    op.execute(f'DROP TRIGGER IF EXISTS trg_soft_delete_project_cascade ON "project";')
    op.execute(f'DROP FUNCTION IF EXISTS soft_delete_project_cascade();')
