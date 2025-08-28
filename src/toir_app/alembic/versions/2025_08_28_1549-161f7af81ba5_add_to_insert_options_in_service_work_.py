"""add to_insert options in service_work cards

Revision ID: 161f7af81ba5
Revises: 62781e81507f
Create Date: 2025-08-28 15:49:14.295960

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '161f7af81ba5'
down_revision: Union[str, None] = '62781e81507f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('servicework', schema=None) as batch_op:
        batch_op.add_column(sa.Column('to_insert', sa.Boolean(), nullable=True, comment='Карточка обработана оператором (внесены материалы и люди)'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('servicework', schema=None) as batch_op:
        batch_op.drop_column('to_insert')
