"""add logo bg/border color

Revision ID: fb59380fa08b
Revises: 0a04611fc748
Create Date: 2023-08-14 06:21:30.512094

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel # added


# revision identifiers, used by Alembic.
revision = 'fb59380fa08b'
down_revision = '0a04611fc748'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('source', schema=None) as batch_op:
        batch_op.add_column(sa.Column('logo_background_color', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.add_column(sa.Column('logo_border_color', sqlmodel.sql.sqltypes.AutoString(), nullable=True))

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('source', schema=None) as batch_op:
        batch_op.drop_column('logo_border_color')
        batch_op.drop_column('logo_background_color')

    # ### end Alembic commands ###