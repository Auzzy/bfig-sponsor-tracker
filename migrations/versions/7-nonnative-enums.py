"""Convert all enums to non-native for compatibility and ease of use. Note that
downgrading this revision will have no effect.

Revision ID: nonnative-enums
Revises: asset-request
Create Date: 2015-04-18 15:10:38.427077

"""

# revision identifiers, used by Alembic.
revision = 'nonnative-enums'
down_revision = 'asset-request'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from sponsortracker import data, model


def _make_enum_nonnative(table, colname, enumname, *values, **alter_column_kwargs):
    op.alter_column(table, colname, existing_type=sa.Enum(name=enumname), type_=sa.Text())
    op.drop_constraint(enumname, table)
    op.alter_column(table, colname, existing_type=sa.Text(), type_=sa.Enum(name=enumname, native_enum=False, *values), **alter_column_kwargs)

def upgrade():
    # Convert all enum columns to using varchar and a constraint, as there's
    # limited native enum support across DBs, and it's mediocre at best
    _make_enum_nonnative('sponsor', 'type', 'SponsorType', 'DIGITAL_AAA_DEV', 'DIGITAL_INDIE_DEV', 'DIGITAL_PUBLISHER', 'MEDIA', 'PRODUCTS', 'SCHOOLS_INSTITUTIONS', 'TABLETOP_DESIGNER', 'TABLETOP_INDIE_DEV', 'TABLETOP_PUBLISHER', nullable=True)
    _make_enum_nonnative('sponsor', 'level', 'LevelType', 'INDIE', 'COPPER', 'SILVER', 'GOLD', 'PLATINUM', 'SERVICE', 'CHARITY', nullable=True)
    _make_enum_nonnative('asset', 'type', 'AssetType', 'DIGITAL_BANNER', 'DIGITAL_MENU', 'LOGO', 'NEWSLETTER_HEADER', 'NEWSLETTER_SIDEBAR', 'NEWSLETTER_FOOTER', 'PROGRAM_QUARTER', 'PROGRAM_HALF', 'PROGRAM_WHOLE', 'PROGRAM_DOUBLE', 'WEBSITE_SIDEBAR', nullable=False)
    _make_enum_nonnative('user', 'type', 'UserType', 'admin', 'coord', 'exec', 'marketing', 'sales', nullable=False)

    
def downgrade():
    pass
