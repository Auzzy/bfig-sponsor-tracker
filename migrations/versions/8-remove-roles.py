"""empty message

Revision ID: remove-roles
Revises: nonnative-enums
Create Date: 2015-04-20 22:33:16.607551

"""

# revision identifiers, used by Alembic.
revision = 'remove-roles'
down_revision = 'nonnative-enums'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from sponsortracker import model


def upgrade():
    op.drop_table('user_roles')
    op.drop_table('role')
    
    op.alter_column('user', 'type', new_column_name='type_name')
    
    op.alter_column('user', 'type_name', existing_type=sa.Enum(name='UserType', native_enum=False), type_=sa.Text())
    
    # Need to change the case of the data, as I was storing the value and not the name.
    # 
    # Creating a new session for modifying data is necessary to prevent
    # PostgreSQL from locking up due to being in a transaction.
    Session = sessionmaker(bind=op.get_bind())
    session = Session()
    
    for user in session.query(model.User).all():
        user.type_name = user.type_name.upper()
    
    session.commit()
    
    type_enum = sa.Enum('ADMIN', 'MARKETING', 'MARKETING_ADMIN', 'SALES', 'SALES_ADMIN', name='UserType', native_enum=False)
    op.alter_column('user', 'type_name', existing_type=sa.Text(), type_=type_enum, nullable=False)

def downgrade():
    op.create_table('role',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('type', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('id', name='role_pkey')
    )
    op.create_table('user_roles',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('role_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], name='user_roles_role_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='user_roles_user_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='user_roles_pkey')
    )
    
    op.alter_column('user', 'type_name', existing_type=sa.Enum(name='UserType', native_enum=False), type_=sa.Text())
    
    # Need to change the case of the data, as I was storing the value and not the name.
    # 
    # Creating a new session for modifying data is necessary to prevent
    # PostgreSQL from locking up due to being in a transaction.
    Session = sessionmaker(bind=op.get_bind())
    session = Session()
    
    for user in session.query(model.User).all():
        user.type_name = user.type_name.lower()
    
    session.commit()
    
    type_enum = sa.Enum('admin', 'coord', 'exec', 'marketing', 'sales', name='UserType', native_enum=False)
    op.alter_column('user', 'type_name', existing_type=sa.Text(), type_=type_enum, nullable=False)
    op.alter_column('user', 'type_name', new_column_name='type')