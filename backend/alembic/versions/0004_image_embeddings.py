"""post_image_embeddings: vectores CLIP de imágenes (búsqueda visual)

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

IMAGE_EMBEDDING_DIM = 512  # CLIP ViT-B/32


def upgrade() -> None:
    op.create_table(
        "post_image_embeddings",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.BigInteger(), sa.ForeignKey("posts.id"), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(IMAGE_EMBEDDING_DIM), nullable=False),
    )
    op.create_index("ix_post_image_embeddings_post_id", "post_image_embeddings", ["post_id"])
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_post_image_embeddings_hnsw "
        "ON post_image_embeddings USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_post_image_embeddings_hnsw")
    op.drop_index("ix_post_image_embeddings_post_id", table_name="post_image_embeddings")
    op.drop_table("post_image_embeddings")
