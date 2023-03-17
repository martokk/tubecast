from typing import TYPE_CHECKING, Any

import datetime

from pydantic import root_validator
from sqlmodel import Field, Relationship, SQLModel

from app.core.uuid import generate_uuid_from_url
from app.handlers import get_handler_from_url
from app.models.source_video_link import SourceVideoLink

from .common import TimestampModel

if TYPE_CHECKING:
    from .source import Source  # pragma: no cover


async def generate_video_id_from_url(url: str) -> str:
    handler = get_handler_from_url(url=url)
    sanitized_video_url = handler.sanitize_video_url(url=url)
    return generate_uuid_from_url(url=sanitized_video_url)


class VideoBase(TimestampModel, SQLModel):
    id: str = Field(default=None, primary_key=True, nullable=False)
    # source_id: str = Field(default=None, foreign_key="source.id", nullable=False)
    handler: str = Field(default=None, nullable=False)
    uploader: str | None = Field(default=None)
    uploader_id: str | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    duration: int | None = Field(default=None)
    thumbnail: str | None = Field(default=None)
    url: str = Field(default=None, nullable=False)
    media_url: str | None = Field(default=None)
    feed_media_url: str | None = Field(default=None)
    media_filesize: int | None = Field(default=None)
    released_at: datetime.datetime = Field(default=None)


class Video(VideoBase, table=True):
    # sources: list["Source"] = Relationship(back_populates="videos")

    sources: list["Source"] = Relationship(
        back_populates="videos",
        link_model=SourceVideoLink,
        sa_relationship_kwargs={"cascade": "delete"},
    )

    def __repr__(self) -> str:
        return f"Video(id={self.id}, title={self.title[:20] if self.title else ''}, handler={self.handler})"

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Video):
            return self.id == other.id
        return False


class VideoCreate(VideoBase):
    @root_validator(pre=True)
    @classmethod
    def set_pre_validation_defaults(cls, values: dict[str, Any]) -> dict[str, Any]:
        handler = get_handler_from_url(url=values["url"])
        sanitized_url = handler.sanitize_video_url(url=values["url"])
        video_id = generate_uuid_from_url(url=sanitized_url)
        feed_media_url = f"/media/{video_id}"
        return {
            **values,
            "handler": handler.name,
            "url": sanitized_url,
            "id": video_id,
            "feed_media_url": feed_media_url,
            "updated_at": datetime.datetime.now(tz=datetime.timezone.utc),
        }


class VideoUpdate(VideoBase):
    pass


class VideoRead(VideoBase):
    pass
