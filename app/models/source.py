from typing import TYPE_CHECKING, Any

from enum import Enum

from pydantic import root_validator
from sqlmodel import Field, Relationship, SQLModel, desc

from app.core.uuid import generate_uuid_from_url
from app.handlers import get_handler_from_url
from app.models.source_video import SourceVideoLink, SourceOrderBy

from .common import TimestampModel

if TYPE_CHECKING:
    from .user import User  # pragma: no cover
    from .video import Video  # pragma: no cover


async def generate_source_id_from_url(url: str) -> str:
    handler = get_handler_from_url(url=url)
    sanitized_source_url = handler.sanitize_source_url(url=url)
    return generate_uuid_from_url(url=sanitized_source_url)


class SourceBase(TimestampModel, SQLModel):
    id: str = Field(default=None, primary_key=True, index=True)
    created_by: str = Field(default=None, foreign_key="user.id", nullable=False)
    url: str = Field(default=None)
    name: str = Field(default=None)
    author: str = Field(default=None)
    logo: str = Field(default=None)
    description: str = Field(default=None)
    ordered_by: str = Field(default=None)
    feed_url: str = Field(default=None)
    extractor: str = Field(default=None)
    handler: str = Field(default=None)
    service: str = Field(default=None)


class Source(SourceBase, table=True):
    videos: list["Video"] = Relationship(
        back_populates="sources",
        link_model=SourceVideoLink,
        sa_relationship_kwargs={"order_by": desc("released_at"), "cascade": "delete"},
    )
    created_user: "User" = Relationship(back_populates="sources")

    def videos_sorted(self) -> list["Video"]:
        if self.ordered_by == SourceOrderBy.RELEASED_AT.value:
            return sorted(self.videos, key=lambda video: video.released_at, reverse=True)
        elif self.ordered_by == SourceOrderBy.CREATED_AT.value:
            return sorted(self.videos, key=lambda video: video.created_at, reverse=True)
        else:
            raise ValueError(f"Invalid order_by value: {self.ordered_by}")


class SourceCreate(SourceBase):
    @root_validator(pre=True)
    @classmethod
    def set_pre_validation_defaults(cls, values: dict[str, Any]) -> dict[str, Any]:
        handler = get_handler_from_url(url=values["url"])
        service = handler.SERVICE_NAME
        sanitized_url = handler.sanitize_source_url(url=values["url"])
        source_id = generate_uuid_from_url(url=sanitized_url)
        feed_url = f"/feed/{source_id}"
        ordered_by = handler.get_ordered_by(url=sanitized_url)
        return {
            **values,
            "handler": handler.name,
            "service": service,
            "url": sanitized_url,
            "id": source_id,
            "feed_url": feed_url,
            "ordered_by": ordered_by,
        }


class SourceUpdate(SourceBase):
    pass


class SourceRead(SourceBase):
    pass
