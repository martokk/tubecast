from typing import Any

from sqlmodel import SQLModel


class FetchResults(SQLModel):
    sources: int = 0
    added_videos: int = 0
    deleted_videos: int = 0
    refreshed_videos: int = 0

    def __add__(self, other: Any) -> "FetchResults":
        """
        Add two FetchResults together.

        Args:
            other (Any): The other FetchResults object.

        Returns:
            FetchResults: The sum of the two FetchResults objects.

        Raises:
            TypeError: If the other object is not a FetchResults object.
        """
        if not isinstance(other, FetchResults):
            raise TypeError(f"can't add FetchResult and {type(other)}")
        return FetchResults(
            sources=self.sources + other.sources,
            added_videos=self.added_videos + other.added_videos,
            deleted_videos=self.deleted_videos + other.deleted_videos,
            refreshed_videos=self.refreshed_videos + other.refreshed_videos,
        )
