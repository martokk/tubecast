from datetime import timedelta

import pytest
from sqlmodel import Session

from app import models
from app.models import Source
from app.models.source_video_link import SourceOrderBy


async def test_source_videos_sorted(db: Session, source_1_w_videos: models.Source) -> None:
    """
    Test Source.videos_sorted() if ordered_by is RELEASED_AT.
    """
    # move last video to first so they are sorted
    last_video = source_1_w_videos.videos.pop(0)
    last_video.released_at = last_video.released_at + timedelta(days=365)
    source_1_w_videos.videos.insert(0, last_video)

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


async def test_source_name_sortable():
    assert Source(name="Name").name_sortable == "Name"
    assert Source(name="T Name").name_sortable == "T Name"
    assert Source(name="Th Name").name_sortable == "Th Name"
    assert Source(name="The Name").name_sortable == "Name"
    assert Source(name="Then Name").name_sortable == "Then Name"
    assert Source(name="The Test").name_sortable == "Test"

    assert Source(name="Timcast Daily Show").name_sortable == "Timcast Daily Show"
    assert Source(name="Timcast IRL").name_sortable == "Timcast IRL"
    assert Source(name="TMJ4 News").name_sortable == "TMJ4 News"
