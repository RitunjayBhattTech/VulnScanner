"""Add AttackChain table and new AI analysis columns to findings

Revision ID: 002
Revises: 001
Create Date: 2026-06-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to findings
    op.add_column("findings", sa.Column("ai_cvss_score", sa.Float(), nullable=True))
    op.add_column("findings", sa.Column("ai_false_positive_reasoning", sa.String(), nullable=True))
    op.add_column("findings", sa.Column("ai_exploitation_notes", sa.String(), nullable=True))

    # Create attack_chains table
    op.create_table(
        "attack_chains",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scan_id", sa.Integer(), nullable=False),
        sa.Column("chain_description", sa.String(), nullable=False),
        sa.Column("steps", postgresql.JSON(), nullable=False),
        sa.Column("severity", sa.String(), nullable=True),
        sa.Column("likelihood", sa.String(), nullable=True),
        sa.Column("mitre_technique_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_attack_chains_id"), "attack_chains", ["id"], unique=False)
    op.create_index(op.f("ix_attack_chains_scan_id"), "attack_chains", ["scan_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_attack_chains_scan_id"), table_name="attack_chains")
    op.drop_index(op.f("ix_attack_chains_id"), table_name="attack_chains")
    op.drop_table("attack_chains")
    op.drop_column("findings", "ai_exploitation_notes")
    op.drop_column("findings", "ai_false_positive_reasoning")
    op.drop_column("findings", "ai_cvss_score")