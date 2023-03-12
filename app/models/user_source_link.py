from sqlmodel import Field, SQLModel

from app.models.common import TimestampModel


class UserSourceLink(TimestampModel, SQLModel, table=True):
    user_id: str | None = Field(default=None, foreign_key="user.id", primary_key=True)
    source_id: str | None = Field(default=None, foreign_key="source.id", primary_key=True)
