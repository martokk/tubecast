from typing import TYPE_CHECKING, Any

import re
from datetime import datetime, timedelta
from enum import Enum

from pydantic import root_validator
from sqlmodel import Field, Relationship, SQLModel

from app.core.uuid import generate_uuid_random

from .common import TimestampModel

if TYPE_CHECKING:
    from .filter import Filter  # pragma: no cover
    from .video import Video  # pragma: no cover


class CriteriaField(Enum):
    RELEASED = "released"
    CREATED = "created"
    DURATION = "duration"
    KEYWORD = "keyword"


class CriteriaOperator(Enum):
    WITHIN = "within"
    SHORTER_THAN = "shorter_than"
    LONGER_THAN = "longer_than"
    MUST_CONTAIN = "must_contain"
    MUST_NOT_CONTAIN = "must_not_contain"


class CriteriaUnitOfMeasure(Enum):
    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"


class CriteriaBase(TimestampModel, SQLModel):
    id: str = Field(default=None, primary_key=True, index=True)
    filter_id: str = Field(default=None, foreign_key="filter.id", index=True, nullable=False)
    field: str = Field(default=None)
    operator: str = Field(default=None)
    value: str = Field(default=None)
    unit_of_measure: str = Field(default=None)

    @property
    def name(self) -> str:
        return (
            f"{self.field} {self.operator} {self.value}" + f" {self.unit_of_measure}"
            if self.unit_of_measure
            else ""
        )


class Criteria(CriteriaBase, table=True):
    filter: "Filter" = Relationship(back_populates="criterias")

    def filter_videos(self, videos: list["Video"]) -> list["Video"]:
        """
        Filter videos by criteria

        Args:
            videos (list[Video]): List of videos to filter

        Returns:
            list[Video]: Filtered list of videos
        """
        filtered_videos = []
        for video in videos:
            if self.field in [CriteriaField.RELEASED.value, CriteriaField.CREATED.value]:
                attr = "released_at" if self.field == CriteriaField.RELEASED.value else "created_at"
                video_dt = getattr(video, attr)
                if not self.is_within_timedelta(
                    dt=video_dt,
                    value=int(self.value),
                    unit_of_measure=self.unit_of_measure,
                ):
                    continue
            elif self.field == CriteriaField.DURATION.value:
                if not self.is_within_duration(
                    video_duration=video.duration,
                    operator=self.operator,
                    value=int(self.value),
                    unit_of_measure=self.unit_of_measure,
                ):
                    continue
            elif self.field == CriteriaField.KEYWORD.value:
                if not self.matches_contains(
                    video=video,
                    keyword=str(self.value),
                ):
                    continue

            filtered_videos.append(video)
        return filtered_videos

    def is_within_timedelta(self, dt: datetime, value: int, unit_of_measure: str) -> bool:
        """
        Check if datetime is within timedelta

        Args:
            dt (datetime): Datetime to check
            value (int): Value of timedelta
            unit_of_measure (str): Unit of measure for timedelta

        Returns:
            bool: True if datetime is within timedelta, False otherwise
        """

        now = datetime.utcnow()
        if unit_of_measure == CriteriaUnitOfMeasure.SECONDS.value:
            within_range = now - timedelta(seconds=value)
        if unit_of_measure == CriteriaUnitOfMeasure.MINUTES.value:
            within_range = now - timedelta(minutes=value)
        elif unit_of_measure == CriteriaUnitOfMeasure.HOURS.value:
            within_range = now - timedelta(hours=value)
        elif unit_of_measure == CriteriaUnitOfMeasure.DAYS.value:
            within_range = now - timedelta(days=value)
        else:
            raise ValueError("Unit of measure must be 'minutes', 'hours' or 'days'")
        return dt >= within_range

    def is_within_duration(
        self, video_duration: int | None, operator: str, value: int, unit_of_measure: str
    ) -> bool:
        """
        Check if video duration is within value.
        If video duration is missing, return True.

        Args:
            video_duration (int): Video duration in seconds
            operator (str): Operator to use for comparison
            value (int): Value to compare video duration to
            unit_of_measure (str): Unit of measure for value

        Returns:
            bool: True if video duration is within value, False otherwise
        """
        if not video_duration:  # if missing duration
            return True

        if unit_of_measure == CriteriaUnitOfMeasure.SECONDS.value:
            seconds = value
        elif unit_of_measure == CriteriaUnitOfMeasure.MINUTES.value:
            seconds = value * 60
        elif unit_of_measure == CriteriaUnitOfMeasure.HOURS.value:
            seconds = value * 60 * 60
        elif unit_of_measure == CriteriaUnitOfMeasure.DAYS.value:
            seconds = value * 60 * 60 * 24
        else:
            raise ValueError("Unit of measure must be 'minutes', 'hours' or 'days'")

        if operator == CriteriaOperator.SHORTER_THAN.value:
            return video_duration <= seconds
        elif operator == CriteriaOperator.LONGER_THAN.value:
            return video_duration > seconds
        else:
            raise ValueError("Operator must be 'shorter_than' or 'longer_than'")

    def matches_contains(self, video: "Video", keyword: str) -> bool:
        """
        Check if video title or description contains keyword

        Args:
            video (Video): Video to check
            keyword (str): Keyword to check for

        Returns:

        """
        match = None

        if self.operator == CriteriaOperator.MUST_CONTAIN.value:
            match = bool(re.search(rf"\b{re.escape(keyword.lower())}\b", str(video.title).lower()))
        elif self.operator == CriteriaOperator.MUST_NOT_CONTAIN.value:
            match = (
                bool(re.search(rf"\b{re.escape(keyword.lower())}\b", str(video.title).lower()))
                is False
            )
        else:
            raise ValueError("Operator must be 'must_contain' or 'must_not_contain'")

        return match


class CriteriaCreate(CriteriaBase):
    @root_validator(pre=True)
    @classmethod
    def set_pre_validation_defaults(cls, values: dict[str, Any]) -> dict[str, Any]:
        field = values["field"]

        if field in [CriteriaField.RELEASED.value, CriteriaField.CREATED.value]:
            if values["operator"] not in [CriteriaOperator.WITHIN.value]:
                raise ValueError("Operator for 'released' and 'created' fields must be 'within'")

        elif field == CriteriaField.DURATION.value:
            if values["operator"] not in [
                CriteriaOperator.SHORTER_THAN.value,
                CriteriaOperator.LONGER_THAN.value,
            ]:
                raise ValueError(
                    "Operator for 'duration' field must be 'shorter_than' or 'longer_than'"
                )

        elif field == CriteriaField.KEYWORD.value:
            if values["operator"] not in [
                CriteriaOperator.MUST_CONTAIN.value,
                CriteriaOperator.MUST_NOT_CONTAIN.value,
            ]:
                raise ValueError(
                    "Operator for 'keyword' field must be 'must_contain' or 'must_not_contain'"
                )

        else:
            raise ValueError("Field must be 'released', 'created', 'duration' or 'keyword'")

        values["value"] = str(values["value"])
        return {
            **values,
            "id": generate_uuid_random(),
        }


class CriteriaUpdate(CriteriaBase):
    pass


class CriteriaRead(CriteriaBase):
    pass
