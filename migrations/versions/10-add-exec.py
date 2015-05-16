"""empty message

Revision ID: add-exec
Revises: move-assets
Create Date: 2015-05-16 15:23:00.080124

"""

# revision identifiers, used by Alembic.
revision = 'add-exec'
down_revision = 'move-assets'

from alembic import op
import sqlalchemy as sa


def upgrade():
    old_type = sa.Enum(name="UserType", native_enum=False)
    new_type = sa.Enum('ADMIN', 'EXEC', 'MARKETING', 'MARKETING_ADMIN', 'SALES', 'SALES_ADMIN', name='UserType', native_enum=False)
    op.alter_column("user", "type_name", existing_type=old_type, type_=new_type)


def downgrade():
    old_type = sa.Enum(name="UserType", native_enum=False)
    new_type = sa.Enum('ADMIN', 'MARKETING', 'MARKETING_ADMIN', 'SALES', 'SALES_ADMIN', name='UserType', native_enum=False)
    op.alter_column("user", "type_name", existing_type=old_type, type_=new_type)