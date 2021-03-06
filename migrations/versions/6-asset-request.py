"""Added table for tracking asset requests

Revision ID: asset-request
Revises: request-ready
Create Date: 2015-04-13 02:34:57.156507

"""

# revision identifiers, used by Alembic.
revision = 'asset-request'
down_revision = 'request-ready'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from sponsortracker import model


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('asset_request',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deal_id', sa.Integer(), nullable=True),
        sa.Column('ready', sa.Boolean(), nullable=True),
        sa.Column('sent', sa.Date(), nullable=True),
        sa.Column('received', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['deal_id'], ['deal.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###

    # Creating a new session for modifying data is necessary to prevent
    # PostgreSQL from locking up due to being in a transaction.
    Session = sessionmaker(bind=op.get_bind())
    session = Session()
    
    for deal in session.query(model.Deal).all():
        if not deal.asset_request:
            deal.asset_request = model.AssetRequest(deal.id)
    
    session.commit()

def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('asset_request')
    ### end Alembic commands ###
