"""post_faces: embeddings de caras detectadas (búsqueda por similitud facial)

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FACE_EMBEDDING_DIM = 512  # facenet InceptionResnetV1 (VGGFace2)


def upgrade() -> None:
    op.create_table(
        "post_faces",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.BigInteger(), sa.ForeignKey("posts.id"), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("face_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bbox", sa.JSON(), nullable=True),
        sa.Column("embedding", Vector(FACE_EMBEDDING_DIM), nullable=False),
    )
    op.create_index("ix_post_faces_post_id", "post_faces", ["post_id"])
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_post_faces_hnsw "
        "ON post_faces USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_post_faces_hnsw")
    op.drop_index("ix_post_faces_post_id", table_name="post_faces")
    op.drop_table("post_faces")
