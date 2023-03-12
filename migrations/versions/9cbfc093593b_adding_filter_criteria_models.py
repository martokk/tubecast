"""adding Filter & Criteria models

Revision ID: 9cbfc093593b
Revises: d8d032f0f6cf
Create Date: 2023-03-08 16:13:33.554706

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel # added


# revision identifiers, used by Alembic.
revision = '9cbfc093593b'
down_revision = 'd8d032f0f6cf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('filter',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_by', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('source_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('filter_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('ordered_by', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    sa.ForeignKeyConstraint(['source_id'], ['source.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('filter', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_filter_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_filter_source_id'), ['source_id'], unique=False)

    op.create_table('criteria',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('filter_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['filter_id'], ['filter.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('criteria', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_criteria_filter_id'), ['filter_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_criteria_id'), ['id'], unique=False)

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('criteria', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_criteria_id'))
        batch_op.drop_index(batch_op.f('ix_criteria_filter_id'))

    op.drop_table('criteria')
    with op.batch_alter_table('filter', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_filter_source_id'))
        batch_op.drop_index(batch_op.f('ix_filter_id'))

    op.drop_table('filter')
    # ### end Alembic commands ###
