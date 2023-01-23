from typing import TYPE_CHECKING, Any

import datetime

from pydantic import root_validator
from sqlmodel import Field, Relationship, SQLModel

from tubecast.core.uuid import generate_uuid_from_url

from .common import TimestampModel

if TYPE_CHECKING:
    from .user import User  # pragma: no cover


class SourceBase(TimestampModel, SQLModel):
    id: str = Field(default=None, primary_key=True, nullable=False)
    uploader: str = Field(default=None)
    uploader_id: str = Field(default=None)
    title: str = Field(default=None)
    description: str = Field(default=None)
    duration: int = Field(default=None)
    thumbnail: str = Field(default=None)
    url: str = Field(default=None)
    # added_at: datetime.datetime = Field(default=None)
    owner_id: str = Field(foreign_key="user.id", nullable=False, default=None)
    # updated_at: datetime.datetime = Field(default=None)


class source(SourceBase, table=True):
    owner: "User" = Relationship(back_populates="sources")


class SourceCreate(SourceBase):
    @root_validator(pre=True)
    @classmethod
    def set_pre_validation_defaults(cls, values: dict[str, Any]) -> dict[str, Any]:
        sanitized_url = values["url"]
        source_uuid = generate_uuid_from_url(url=sanitized_url)
        return {
            **values,
            "url": sanitized_url,
            "id": values.get("id", source_uuid),
            "updated_at": datetime.datetime.now(tz=datetime.timezone.utc),
        }


class SourceUpdate(SourceBase):
    pass


class SourceRead(SourceBase):
    pass
