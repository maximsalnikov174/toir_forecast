"""add_bom

Revision ID: 8db48191e582
Revises: a33f215bb3fa
Create Date: 2025-08-26 11:17:56.844969

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8db48191e582'
down_revision: Union[str, None] = 'a33f215bb3fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'maintenancebillofmaterials',
        sa.Column('delivery', sa.Integer(), nullable=False, comment='Номер доставки, оформленной в OeBS'),
        sa.Column('bar_code', sa.String(length=15), nullable=False, comment='Штрих-код документа'),
        sa.Column('from_organization', sa.Integer(), nullable=False, comment='Ссылка на подразделение, с которого произошло списание'),
        sa.Column('service_work_id', sa.Integer(), nullable=False, comment='Ссылка на карточку работы, для которой предназначены материалы'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='Пользователь, загрузивший документ'),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(['from_organization'], ['organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['service_work_id'], ['servicework.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bar_code'),
        sa.UniqueConstraint('delivery')
    )
    with op.batch_alter_table('maintenancebillofmaterials', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_maintenancebillofmaterials_from_organization'), ['from_organization'], unique=False)
        batch_op.create_index(batch_op.f('ix_maintenancebillofmaterials_service_work_id'), ['service_work_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_maintenancebillofmaterials_user_id'), ['user_id'], unique=False)

    op.create_table(
        'maintenancecomponent',
        sa.Column('snb', sa.String(length=16), nullable=False, comment='СНБ-номер материала'),
        sa.Column('material_name', sa.String(length=300), nullable=False, comment='Наименование материала'),
        sa.Column('material_count', sa.Integer(), nullable=False, comment='Количество использованного материала'),
        sa.Column('maintenance_bom_id', sa.Integer(), nullable=False, comment='Ссылка на документ, в котором указан материал'),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(['maintenance_bom_id'], ['maintenancebillofmaterials.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('maintenancecomponent', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_maintenancecomponent_maintenance_bom_id'), ['maintenance_bom_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('maintenancecomponent', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_maintenancecomponent_maintenance_bom_id'))

    op.drop_table('maintenancecomponent')

    with op.batch_alter_table('maintenancebillofmaterials', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_maintenancebillofmaterials_user_id'))
        batch_op.drop_index(batch_op.f('ix_maintenancebillofmaterials_service_work_id'))
        batch_op.drop_index(batch_op.f('ix_maintenancebillofmaterials_from_organization'))

    op.drop_table('maintenancebillofmaterials')
