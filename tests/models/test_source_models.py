from datetime import timedelta

import pytest
from sqlmodel import Session

from app import models
from app.models.source_video_link import SourceOrderBy


async def test_source_videos_sorted(db: Session, source_1_w_videos: models.Source) -> None:
    """
    Test Source.videos_sorted() if ordered_by is RELEASED_AT.
    """
    ordered_by = SourceOrderBy.RELEASED_AT.value

    # Assert videos are already sorted.
    source_videos = source_1_w_videos.videos.copy()
    assert source_1_w_videos.videos_sorted(ordered_by=ordered_by) == source_videos

    # Change created_at of first video. Move to end of list.
    first_video = source_1_w_videos.videos.pop(0)
    first_video.created_at = first_video.created_at - timedelta(days=1000)
    source_1_w_videos.videos.append(first_video)
    assert source_1_w_videos.videos != source_videos
    assert first_video == source_1_w_videos.videos[-1]

    # Sort videos by released_at
    sorted_videos = source_1_w_videos.videos_sorted(ordered_by=SourceOrderBy.RELEASED_AT.value)
    assert sorted_videos == source_videos
    assert first_video == sorted_videos[0]

    # Sort videos by created_at
    sorted_videos = source_1_w_videos.videos_sorted(ordered_by=SourceOrderBy.CREATED_AT.value)
    assert first_video == sorted_videos[1]

    # Test invalid ordered_by
    with pytest.raises(ValueError):
        source_1_w_videos.videos_sorted(ordered_by="invalid")
