"""add tg_account for user

Revision ID: 4478ac2de337
Revises: f33a7c9883c7
Create Date: 2025-09-10 20:49:15.635283

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4478ac2de337'
down_revision: Union[str, None] = 'f33a7c9883c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'tg_id',
                sa.BigInteger(),
                nullable=True,
                comment='Телеграм-аккаунт пользователя'
            )
        )
        batch_op.create_index(
            batch_op.f('ix_user_tg_id'), ['tg_id'], unique=True
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_tg_id'))
        batch_op.drop_column('tg_id')
