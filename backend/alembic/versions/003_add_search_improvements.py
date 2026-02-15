"""add search improvements (title, transcript, search_vector)

Revision ID: 003_search_v2
Revises: 002_add_status
Create Date: V2 - Search accuracy improvements

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR

revision: str = "003_search_v2"
down_revision: Union[str, None] = "002_add_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Video başlığı kolonu
    op.add_column("videos", sa.Column("title", sa.Text(), nullable=True))
    
    # Ses transkripti kolonu
    op.add_column("videos", sa.Column("transcript", sa.Text(), nullable=True))
    
    # Full-text search için tsvector kolonu
    op.add_column("videos", sa.Column("search_vector", TSVECTOR(), nullable=True))
    
    # GIN index for full-text search
    op.create_index(
        "idx_videos_search_vector",
        "videos",
        ["search_vector"],
        postgresql_using="gin"
    )
    
    # Trigger: search_vector'ü otomatik güncelle
    op.execute("""
        CREATE OR REPLACE FUNCTION videos_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := 
                setweight(to_tsvector('pg_catalog.simple', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('pg_catalog.simple', coalesce(NEW.description_ai, '')), 'B') ||
                setweight(to_tsvector('pg_catalog.simple', coalesce(NEW.transcript, '')), 'C') ||
                setweight(to_tsvector('pg_catalog.simple', coalesce(NEW.description_manual, '')), 'B');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER videos_search_vector_trigger
        BEFORE INSERT OR UPDATE ON videos
        FOR EACH ROW EXECUTE FUNCTION videos_search_vector_update();
    """)
    
    # Mevcut videoların search_vector'ünü güncelle
    op.execute("""
        UPDATE videos SET 
            search_vector = 
                setweight(to_tsvector('pg_catalog.simple', coalesce(title, '')), 'A') ||
                setweight(to_tsvector('pg_catalog.simple', coalesce(description_ai, '')), 'B') ||
                setweight(to_tsvector('pg_catalog.simple', coalesce(transcript, '')), 'C') ||
                setweight(to_tsvector('pg_catalog.simple', coalesce(description_manual, '')), 'B');
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS videos_search_vector_trigger ON videos")
    op.execute("DROP FUNCTION IF EXISTS videos_search_vector_update()")
    op.drop_index("idx_videos_search_vector", table_name="videos")
    op.drop_column("videos", "search_vector")
    op.drop_column("videos", "transcript")
    op.drop_column("videos", "title")
