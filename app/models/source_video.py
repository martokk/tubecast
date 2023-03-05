from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .source import Source  # pragma: no cover
    from .video import Video  # pragma: no cover


class SourceVideoLink(SQLModel, table=True):
    source_id: str | None = Field(default=None, foreign_key="source.id", primary_key=True)
    video_id: str | None = Field(default=None, foreign_key="video.id", primary_key=True)

    # source: "Source" = Relationship(back_populates="videos", link_model="source_video_link")
    # video: "Video" = Relationship(back_populates="sources", link_model="source_video_link")
