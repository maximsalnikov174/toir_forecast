"""add to_insert options in BOM

Revision ID: 62781e81507f
Revises: 8db48191e582
Create Date: 2025-08-28 15:35:35.104238

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62781e81507f'
down_revision: Union[str, None] = '8db48191e582'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('maintenancebillofmaterials', schema=None) as batch_op:
        batch_op.add_column(sa.Column('to_insert', sa.Boolean(), nullable=True, comment='Документ обработан оператором'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('maintenancebillofmaterials', schema=None) as batch_op:
        batch_op.drop_column('to_insert')
