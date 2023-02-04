import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel, text

# def uuid4_truncate() -> str:
#     full_uuid = uuid.uuid4()
#     return full_uuid.hex[:8]


# class UUIDModel(SQLModel):
#     uuid: str = Field(
#         default_factory=uuid4_truncate,
#         primary_key=True,
#         index=True,
#         nullable=False,
#         sa_column_kwargs={"server_default": text("gen_random_uuid()"), "unique": True},
#     )


class TimestampModel(SQLModel):
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP"),
        },
    )
