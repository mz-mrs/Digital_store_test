"""change order ids to string

Revision ID: 08d9805afc58
Revises: 4ff1bb3a9f29
Create Date: 2026-09-03 16:08:06.747534

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08d9805afc58'
down_revision: Union[str, Sequence[str], None] = '4ff1bb3a9f29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "order_items_order_id_fkey",
        "order_items",
        type_="foreignkey",
    )

    op.drop_constraint(
        "deliveries_order_id_fkey",
        "deliveries",
        type_="foreignkey",
    )

    op.alter_column(
        "orders",
        "id",
        existing_type=sa.UUID(),
        type_=sa.String(length=255),
        existing_nullable=False,
        postgresql_using="id::text",
    )

    op.alter_column(
        "order_items",
        "order_id",
        existing_type=sa.UUID(),
        type_=sa.String(length=255),
        existing_nullable=False,
        postgresql_using="order_id::text",
    )

    op.alter_column(
        "deliveries",
        "order_id",
        existing_type=sa.UUID(),
        type_=sa.String(length=255),
        existing_nullable=False,
        postgresql_using="order_id::text",
    )

    op.alter_column(
        "payment_events",
        "order_id",
        existing_type=sa.UUID(),
        type_=sa.String(length=255),
        existing_nullable=False,
        postgresql_using="order_id::text",
    )

    op.create_foreign_key(
        "order_items_order_id_fkey",
        "order_items",
        "orders",
        ["order_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "deliveries_order_id_fkey",
        "deliveries",
        "orders",
        ["order_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "order_items_order_id_fkey",
        "order_items",
        type_="foreignkey",
    )

    op.drop_constraint(
        "deliveries_order_id_fkey",
        "deliveries",
        type_="foreignkey",
    )

    op.alter_column(
        "payment_events",
        "order_id",
        existing_type=sa.String(length=255),
        type_=sa.UUID(),
        existing_nullable=False,
        postgresql_using="order_id::uuid",
    )

    op.alter_column(
        "order_items",
        "order_id",
        existing_type=sa.String(length=255),
        type_=sa.UUID(),
        existing_nullable=False,
        postgresql_using="order_id::uuid",
    )

    op.alter_column(
        "deliveries",
        "order_id",
        existing_type=sa.String(length=255),
        type_=sa.UUID(),
        existing_nullable=False,
        postgresql_using="order_id::uuid",
    )

    op.alter_column(
        "orders",
        "id",
        existing_type=sa.String(length=255),
        type_=sa.UUID(),
        existing_nullable=False,
        postgresql_using="id::uuid",
    )

    op.create_foreign_key(
        "order_items_order_id_fkey",
        "order_items",
        "orders",
        ["order_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "deliveries_order_id_fkey",
        "deliveries",
        "orders",
        ["order_id"],
        ["id"],
        ondelete="CASCADE",
    )