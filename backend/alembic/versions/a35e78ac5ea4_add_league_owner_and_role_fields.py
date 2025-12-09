"""add league owner and role fields

Revision ID: a35e78ac5ea4
Revises: fc1bcaffb6b3
Create Date: 2025-12-08 18:31:55.113068

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a35e78ac5ea4'
down_revision: Union[str, None] = 'fc1bcaffb6b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add owner_id column to leagues table if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='leagues' AND column_name='owner_id'
            ) THEN
                ALTER TABLE leagues ADD COLUMN owner_id UUID REFERENCES users(id) ON DELETE CASCADE;
            END IF;
        END $$;
    """)
    
    # Add role column to league_members table if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='league_members' AND column_name='role'
            ) THEN
                ALTER TABLE league_members ADD COLUMN role VARCHAR(20) DEFAULT 'member' NOT NULL;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Remove role column from league_members
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='league_members' AND column_name='role'
            ) THEN
                ALTER TABLE league_members DROP COLUMN role;
            END IF;
        END $$;
    """)
    
    # Remove owner_id column from leagues
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='leagues' AND column_name='owner_id'
            ) THEN
                ALTER TABLE leagues DROP COLUMN owner_id;
            END IF;
        END $$;
    """)
