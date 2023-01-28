from typing import Any

from sqlmodel import SQLModel


class FetchResults(SQLModel):
    added_videos: int = 0
    deleted_videos: int = 0
    refreshed_videos: int = 0

    def __add__(self, other: Any) -> "FetchResults":
        """
        Add two FetchResults together.
        """
        if not isinstance(other, FetchResults):
            raise TypeError(f"can't add FetchResult and {type(other)}")
        return FetchResults(
            added_videos=self.added_videos + other.added_videos,
            deleted_videos=self.deleted_videos + other.deleted_videos,
            refreshed_videos=self.refreshed_videos + other.refreshed_videos,
        )
