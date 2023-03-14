from typing import TYPE_CHECKING, Any

import operator

from pydantic import root_validator
from sqlmodel import Field, Relationship, SQLModel

from app.core.uuid import generate_uuid_random

from .common import TimestampModel
from .criteria import Criteria, CriteriaField, CriteriaOperator  # pragma: no cover

if TYPE_CHECKING:
    from .source import Source  # pragma: no cover
    from .user import User  # pragma: no cover
    from .video import Video  # pragma: no cover


class FilterBase(TimestampModel, SQLModel):
    id: str = Field(default=None, primary_key=True, index=True)
    name: str = Field(default=None)
    source_id: str = Field(default=None, foreign_key="source.id", index=True, nullable=False)
    ordered_by: str = Field(default=None)
    created_by: str = Field(default=None, foreign_key="user.id", nullable=False)


class Filter(FilterBase, table=True):
    created_user: "User" = Relationship()
    source: "Source" = Relationship(back_populates="filters")
    criterias: list["Criteria"] = Relationship(
        back_populates="filter", sa_relationship_kwargs={"cascade": "delete"}
    )

    def videos(self) -> list["Video"]:
        must_contain_criteria = False

        must_contain_videos = []
        for criteria in self.criterias:
            if (
                criteria.field == CriteriaField.KEYWORD.value
                and criteria.operator == CriteriaOperator.MUST_CONTAIN.value
            ):
                must_contain_criteria = True
                must_contain_videos += criteria.filter_videos(videos=self.source.videos)
        must_contain_videos = list(set(must_contain_videos))

        filtered_videos = must_contain_videos if must_contain_criteria else self.source.videos
        filtered_videos = [video for video in filtered_videos if video.released_at]
        for criteria in self.criterias:
            if (
                criteria.field == CriteriaField.KEYWORD.value
                and criteria.operator == CriteriaOperator.MUST_CONTAIN.value
            ):
                continue
            else:
                filtered_videos = criteria.filter_videos(videos=filtered_videos)

        if self.ordered_by:
            filtered_videos.sort(key=operator.attrgetter(self.ordered_by), reverse=True)

        return filtered_videos

    @property
    def feed_url(self) -> str:
        return f"/filter/{self.id}/feed"


class FilterCreate(FilterBase, TimestampModel):
    @root_validator(pre=True)
    @classmethod
    def set_pre_validation_defaults(cls, values: dict[str, Any]) -> dict[str, Any]:
        filter_id = generate_uuid_random()
        return {
            **values,
            "id": filter_id,
        }


class FilterUpdate(FilterBase):
    pass


class FilterRead(FilterBase):
    criterias: list["Criteria"] = Relationship()
