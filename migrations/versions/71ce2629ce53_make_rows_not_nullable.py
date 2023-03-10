"""make rows not Nullable

Revision ID: 71ce2629ce53
Revises: 40d698fcbee5
Create Date: 2023-03-14 17:10:30.980576

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel # added


# revision identifiers, used by Alembic.
revision = '71ce2629ce53'
down_revision = '40d698fcbee5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('video', schema=None) as batch_op:
        batch_op.alter_column('uploader',
               existing_type=sa.VARCHAR(),
               nullable=False)
        batch_op.alter_column('uploader_id',
               existing_type=sa.VARCHAR(),
               nullable=False)
        batch_op.alter_column('title',
               existing_type=sa.VARCHAR(),
               nullable=False)
        batch_op.alter_column('url',
               existing_type=sa.VARCHAR(),
               nullable=False)
        batch_op.alter_column('released_at',
               existing_type=sa.DATETIME(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('video', schema=None) as batch_op:
        batch_op.alter_column('released_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('url',
               existing_type=sa.VARCHAR(),
               nullable=True)
        batch_op.alter_column('title',
               existing_type=sa.VARCHAR(),
               nullable=True)
        batch_op.alter_column('uploader_id',
               existing_type=sa.VARCHAR(),
               nullable=True)
        batch_op.alter_column('uploader',
               existing_type=sa.VARCHAR(),
               nullable=True)

    # ### end Alembic commands ###
