"""Initial schema

Revision ID: eeafe92257f6
Revises:
Create Date: 2025-02-25 17:31:19.739262

"""

import enum
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "eeafe92257f6"
down_revision = None
branch_labels = None
depends_on = None


class InvoiceStatus(enum.Enum):
    """Status of an invoice."""

    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELED = "canceled"


def table_exists(inspector, table_name):
    """Check if a table exists in the database."""
    return table_name in inspector.get_table_names()


def index_exists(inspector, table_name, index_name):
    """Check if an index exists on a table."""
    if not table_exists(inspector, table_name):
        return False
    indexes = inspector.get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def upgrade() -> None:
    # Get database connection and inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # ### commands auto generated by Alembic - please adjust! ###
    if not table_exists(inspector, "clients"):
        op.create_table(
            "clients",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("contact_name", sa.String(), nullable=True),
            sa.Column("email", sa.String(), nullable=True),
            sa.Column("phone", sa.String(), nullable=True),
            sa.Column("address", sa.String(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_clients_name"), "clients", ["name"], unique=False)

    if not table_exists(inspector, "tags"):
        op.create_table(
            "tags",
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=True),
            sa.PrimaryKeyConstraint("name"),
        )

    if not table_exists(inspector, "invoices"):
        op.create_table(
            "invoices",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("client_id", sa.Integer(), nullable=False),
            sa.Column("invoice_number", sa.String(length=50), nullable=False),
            sa.Column("issue_date", sa.Date(), nullable=False),
            sa.Column("due_date", sa.Date(), nullable=False),
            sa.Column(
                "status",
                sa.Enum("DRAFT", "SENT", "PAID", "OVERDUE", "CANCELED", name="invoicestatus"),
                nullable=False,
            ),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("subtotal", sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column("tax_rate", sa.Numeric(precision=5, scale=2), nullable=True),
            sa.Column("tax_amount", sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column("total_amount", sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column("invoice_metadata", sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(
                ["client_id"],
                ["clients.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("invoice_number"),
        )

    if not table_exists(inspector, "projects"):
        op.create_table(
            "projects",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("client_id", sa.Integer(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("hourly_rate", sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("start_date", sa.Date(), nullable=True),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["client_id"],
                ["clients.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_projects_name"), "projects", ["name"], unique=False)

    if not table_exists(inspector, "work_logs"):
        op.create_table(
            "work_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("project_id", sa.Integer(), nullable=False),
            sa.Column("invoice_id", sa.Integer(), nullable=True),
            sa.Column("work_date", sa.Date(), nullable=False),
            sa.Column("hours", sa.Numeric(precision=8, scale=2), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("category", sa.String(), nullable=True),
            sa.Column("billable", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["invoice_id"],
                ["invoices.id"],
            ),
            sa.ForeignKeyConstraint(
                ["project_id"],
                ["projects.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_work_logs_work_date"), "work_logs", ["work_date"], unique=False)

    if not table_exists(inspector, "invoice_items"):
        op.create_table(
            "invoice_items",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("invoice_id", sa.Integer(), nullable=False),
            sa.Column("work_log_id", sa.Integer(), nullable=True),
            sa.Column("description", sa.String(length=255), nullable=False),
            sa.Column("quantity", sa.Numeric(precision=8, scale=2), nullable=False),
            sa.Column("unit", sa.String(length=50), nullable=True),
            sa.Column("rate", sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column("category", sa.String(length=100), nullable=True),
            sa.ForeignKeyConstraint(
                ["invoice_id"],
                ["invoices.id"],
            ),
            sa.ForeignKeyConstraint(
                ["work_log_id"],
                ["work_logs.id"],
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if not table_exists(inspector, "work_log_tag"):
        op.create_table(
            "work_log_tag",
            sa.Column("work_log_id", sa.Integer(), nullable=False),
            sa.Column("tag_name", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(
                ["tag_name"],
                ["tags.name"],
            ),
            sa.ForeignKeyConstraint(
                ["work_log_id"],
                ["work_logs.id"],
            ),
            sa.PrimaryKeyConstraint("work_log_id", "tag_name"),
        )
    # ### end Alembic commands ###


def downgrade() -> None:
    # Get database connection and inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # ### commands auto generated by Alembic - please adjust! ###
    if table_exists(inspector, "work_log_tag"):
        op.drop_table("work_log_tag")

    if table_exists(inspector, "invoice_items"):
        op.drop_table("invoice_items")

    if table_exists(inspector, "work_logs"):
        if index_exists(inspector, "work_logs", "ix_work_logs_work_date"):
            op.drop_index(op.f("ix_work_logs_work_date"), table_name="work_logs")
        op.drop_table("work_logs")

    if table_exists(inspector, "projects"):
        if index_exists(inspector, "projects", "ix_projects_name"):
            op.drop_index(op.f("ix_projects_name"), table_name="projects")
        op.drop_table("projects")

    if table_exists(inspector, "invoices"):
        op.drop_table("invoices")

    if table_exists(inspector, "tags"):
        op.drop_table("tags")

    if table_exists(inspector, "clients"):
        if index_exists(inspector, "clients", "ix_clients_name"):
            op.drop_index(op.f("ix_clients_name"), table_name="clients")
        op.drop_table("clients")
    # ### end Alembic commands ###
