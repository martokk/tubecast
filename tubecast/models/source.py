from typing import TYPE_CHECKING, Any

from enum import Enum

from pydantic import root_validator
from sqlmodel import Field, Relationship, SQLModel

from tubecast.core.uuid import generate_uuid_from_url
from tubecast.handlers import get_handler_from_url

from .common import TimestampModel

if TYPE_CHECKING:
    from .user import User  # pragma: no cover
    from .video import Video  # pragma: no cover


async def generate_source_id_from_url(url: str) -> str:
    handler = get_handler_from_url(url=url)
    sanitized_source_url = handler.sanitize_source_url(url=url)
    return generate_uuid_from_url(url=sanitized_source_url)


class SourceOrderBy(Enum):
    RELEASE = "release"
    ADDED = "added"


class SourceBase(TimestampModel, SQLModel):
    id: str = Field(default=None, primary_key=True, index=True)
    url: str = Field(default=None)
    name: str = Field(default=None)
    author: str = Field(default=None)
    logo: str = Field(default=None)
    description: str = Field(default=None)
    ordered_by: str = Field(default=None)
    feed_url: str = Field(default=None)
    extractor: str = Field(default=None)
    handler: str = Field(default=None)
    created_by: str = Field(default=None, foreign_key="user.id", nullable=False)


class Source(SourceBase, table=True):
    videos: list["Video"] = Relationship(
        back_populates="source",
        sa_relationship_kwargs={
            "cascade": "all, delete",  # Instruct the ORM how to track changes to local objects
        },
    )
    created_user: "User" = Relationship(back_populates="sources")


class SourceCreate(SourceBase):
    @root_validator(pre=True)
    @classmethod
    def set_pre_validation_defaults(cls, values: dict[str, Any]) -> dict[str, Any]:
        handler = get_handler_from_url(url=values["url"])
        sanitized_url = handler.sanitize_source_url(url=values["url"])
        source_id = generate_uuid_from_url(url=sanitized_url)
        feed_url = f"/feed/{source_id}"
        return {
            **values,
            "handler": handler.name,
            "url": sanitized_url,
            "id": source_id,
            "feed_url": feed_url,
            "ordered_by": SourceOrderBy.RELEASE.value,
        }


class SourceUpdate(SourceBase):
    pass


class SourceRead(SourceBase):
    pass