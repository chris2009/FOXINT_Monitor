"""Esquema inicial: pages, posts, detections, post_embeddings, keyword_rules, alerts, users

Revision ID: 0001
Revises:
Create Date: 2026-07-02

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 768  # nomic-embed-text


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "pages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("fb_page_id", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("platform", sa.Text(), nullable=False, server_default="facebook"),
        sa.Column("fan_count", sa.Integer(), nullable=True),
        sa.Column("followers_count", sa.Integer(), nullable=True),
        sa.Column("poll_interval", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "posts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("page_id", sa.BigInteger(), sa.ForeignKey("pages.id"), nullable=False),
        sa.Column("platform_post_id", sa.Text(), nullable=False, unique=True),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("permalink", sa.Text(), nullable=True),
        sa.Column("media_urls", sa.JSON(), nullable=True),
        sa.Column("is_live", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("live_status", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_posts_page_id", "posts", ["page_id"])

    op.create_table(
        "keyword_rules",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("keywords", sa.ARRAY(sa.Text()), nullable=False),
        sa.Column("match_type", sa.Text(), nullable=False, server_default="any"),
        sa.Column("severity", sa.Text(), nullable=False, server_default="medium"),
        sa.Column(
            "notify_channels",
            sa.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{telegram}'"),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "detections",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.BigInteger(), sa.ForeignKey("posts.id"), nullable=False),
        sa.Column("analyzer", sa.Text(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_detections_post_id", "detections", ["post_id"])

    op.create_table(
        "post_embeddings",
        sa.Column("post_id", sa.BigInteger(), sa.ForeignKey("posts.id"), primary_key=True),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.BigInteger(), sa.ForeignKey("posts.id"), nullable=False),
        sa.Column("rule_id", sa.BigInteger(), sa.ForeignKey("keyword_rules.id"), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="sent"),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False, server_default="analyst"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("users")
    op.drop_table("alerts")
    op.drop_table("post_embeddings")
    op.drop_index("ix_detections_post_id", table_name="detections")
    op.drop_table("detections")
    op.drop_table("keyword_rules")
    op.drop_index("ix_posts_page_id", table_name="posts")
    op.drop_table("posts")
    op.drop_table("pages")
