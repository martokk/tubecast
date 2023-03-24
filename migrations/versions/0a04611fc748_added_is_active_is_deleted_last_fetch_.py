"""added is_active, is_deleted, last_fetch_error to Source model

Revision ID: 0a04611fc748
Revises: 79533f595cf1
Create Date: 2023-03-23 15:22:20.556522

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel  # added


# revision identifiers, used by Alembic.
revision = "0a04611fc748"
down_revision = "79533f595cf1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("source", schema=None) as batch_op:
        batch_op.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default=1))
        batch_op.add_column(sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=0))
        batch_op.add_column(
            sa.Column(
                "last_fetch_error",
                sqlmodel.sql.sqltypes.AutoString(),
                nullable=True,
                server_default=None,
            )
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("source", schema=None) as batch_op:
        batch_op.drop_column("last_fetch_error")
        batch_op.drop_column("is_deleted")
        batch_op.drop_column("is_active")

    # ### end Alembic commands ###
