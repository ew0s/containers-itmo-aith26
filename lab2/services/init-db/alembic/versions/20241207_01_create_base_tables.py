"""create base tables

Revision ID: 20241207_01
Revises:
Create Date: 2024-12-07 00:00:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20241207_01"
down_revision = None
branch_labels = None
depends_on = None


message_role_enum = sa.Enum("user", "assistant", "system", name="message_role")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_user_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_users_telegram_user_id", "users", ["telegram_user_id"], unique=True
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("role", message_role_enum, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_messages_created_at", "messages", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_messages_created_at", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_users_telegram_user_id", table_name="users")
    op.drop_table("users")
    message_role_enum.drop(op.get_bind(), checkfirst=True)

