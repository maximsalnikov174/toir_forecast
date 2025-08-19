"""upd model organization

Revision ID: a33f215bb3fa
Revises: 9dcf22735877
Create Date: 2025-08-19 08:58:16.950586

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a33f215bb3fa'
down_revision: Union[str, None] = '9dcf22735877'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('organization', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'station_id',
                sa.Integer(),
                nullable=True,
                comment='Связь с СТО (станцией тех обслуживания)'
            )
        )
        batch_op.create_foreign_key(
            'fk_organization_station_id_station',
            'station',
            ['station_id'],
            ['id'],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('organization', schema=None) as batch_op:
        batch_op.drop_constraint(
            'fk_organization_station_id_station',
            type_='foreignkey',
        )
        batch_op.drop_column('station_id')
