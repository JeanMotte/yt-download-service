"""
Add user and history tables.

Revision ID: ecdad15af032
Revises:
Create Date: 2025-07-25 09:19:04.675567

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "ecdad15af032"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create user and history tables."""
    op.create_table(
        "user",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
    op.create_table(
        "history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("yt_video_url", sa.String(), nullable=False),
        sa.Column("video_title", sa.String(), nullable=False),
        sa.Column("resolution", sa.String(), nullable=True),  # Nullable for audio-only
        sa.Column("format_id", sa.String(), nullable=False),
        sa.Column("start_time", sa.Integer(), nullable=True),  # Nullable for full video
        sa.Column("end_time", sa.Integer(), nullable=True),  # Nullable for full video
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    """Drop user and history tables."""
    op.drop_table("history")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
    # ### end Alembic commands ###
