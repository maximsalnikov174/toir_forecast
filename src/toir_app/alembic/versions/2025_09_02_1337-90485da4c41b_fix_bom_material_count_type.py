"""fix bom material count type

Revision ID: 90485da4c41b
Revises: 161f7af81ba5
Create Date: 2025-09-02 13:37:30.120201

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90485da4c41b'
down_revision: Union[str, None] = '161f7af81ba5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('maintenancecomponent', schema=None) as batch_op:
        batch_op.alter_column('material_count',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('maintenancecomponent', schema=None) as batch_op:
        batch_op.alter_column('material_count',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=False)
