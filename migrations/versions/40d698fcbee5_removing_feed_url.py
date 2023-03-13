"""removing feed_url

Revision ID: 40d698fcbee5
Revises: 94c0ee2d15b0
Create Date: 2023-03-11 15:30:57.603018

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel # added


# revision identifiers, used by Alembic.
revision = '40d698fcbee5'
down_revision = '94c0ee2d15b0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('filter', schema=None) as batch_op:
        batch_op.drop_column('filter_url')

    with op.batch_alter_table('source', schema=None) as batch_op:
        batch_op.drop_column('feed_url')

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('source', schema=None) as batch_op:
        batch_op.add_column(sa.Column('feed_url', sa.VARCHAR(), nullable=True))

    with op.batch_alter_table('filter', schema=None) as batch_op:
        batch_op.add_column(sa.Column('filter_url', sa.VARCHAR(), nullable=True))

    # ### end Alembic commands ###