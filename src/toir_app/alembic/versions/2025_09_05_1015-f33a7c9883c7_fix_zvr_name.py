"""fix zvr name

Revision ID: f33a7c9883c7
Revises: 90485da4c41b
Create Date: 2025-09-05 10:15:50.557854

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f33a7c9883c7'
down_revision: Union[str, None] = '90485da4c41b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'servicework',
        'zrv_number',
        new_column_name='zvr_number'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'servicework',
        'zvr_number',
        new_column_name='zrv_number'
    )
