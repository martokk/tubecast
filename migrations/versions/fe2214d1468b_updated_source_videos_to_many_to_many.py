"""updated source videos to many-to-many

Revision ID: fe2214d1468b
Revises: 64abcf0bff79
Create Date: 2023-03-05 15:58:26.191877

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel  # added


# revision identifiers, used by Alembic.
revision = "fe2214d1468b"
down_revision = "64abcf0bff79"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "sourcevideolink",
        sa.Column("source_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("video_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["source.id"],
        ),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["video.id"],
        ),
        sa.PrimaryKeyConstraint("source_id", "video_id"),
    )
    with op.batch_alter_table("video", schema=None) as batch_op:
        batch_op.drop_constraint("fk_video_source_id_source", type_="foreignkey")
        batch_op.drop_column("source_id")

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("video", schema=None) as batch_op:
        batch_op.add_column(sa.Column("source_id", sa.VARCHAR(), nullable=False))
        batch_op.create_foreign_key("fk_video_source_id_source", "source", ["source_id"], ["id"])

    op.drop_table("sourcevideolink")
    # ### end Alembic commands ###
