"""
Create user and history tables.

Revision ID: 90902160bb77
Revises:
Create Date: 2025-07-19 17:42:21.399073

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "90902160bb77"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create user and history tables."""
    op.create_table(
        "user",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_table(
        "history",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id"),
            nullable=False,
        ),
        sa.Column("yt_video_id", sa.String(), nullable=False),
        sa.Column("start_time", sa.Integer(), nullable=False),
        sa.Column("end_time", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )


def downgrade():
    """Drop user and history tables."""
    op.drop_table("history")
    op.drop_table("user")
