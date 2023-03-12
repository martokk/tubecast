from enum import Enum

from sqlmodel import Field, SQLModel

from app.models.common import TimestampModel


class SourceOrderBy(Enum):
    RELEASED_AT = "released_at"
    CREATED_AT = "created_at"


class SourceVideoLink(TimestampModel, SQLModel, table=True):
    source_id: str | None = Field(default=None, foreign_key="source.id", primary_key=True)
    video_id: str | None = Field(default=None, foreign_key="video.id", primary_key=True)
