"""Fusion des branches de migration

Revision ID: 55a9b4e2f367
Revises: 33d4f5a4e3c3, 606408eb352b
Create Date: 2025-10-15 20:33:09.137257

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '55a9b4e2f367'
down_revision = ('33d4f5a4e3c3', '606408eb352b')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
