from app.models import Video


def test_hash_equality() -> None:
    """
    Test video hash equality.
    """
    # Test that two Videos with the same id have the same hash.
    video1 = Video(id="abc123", title="Test video")
    video2 = Video(id="abc123", title="Different title")
    assert hash(video1) == hash(video2)

    # Test that two Videos with different ids have different hashes
    video1 = Video(id="abc123", title="Test video")
    video2 = Video(id="def456", title="Test video")
    assert hash(video1) != hash(video2)


def test_eq_equality() -> None:
    """
    Test video equality.
    """
    # Test that two Videos with the same id are equal.
    video1 = Video(id="abc123", title="Test video")
    video2 = Video(id="abc123", title="Different title")
    assert video1 == video2

    # Test that two Videos with different ids are not equal.
    video1 = Video(id="abc123", title="Test video")
    video2 = Video(id="def456", title="Test video")
    assert not (video1 == video2)

    # Test a non-Video object
    video1 = Video(id="abc123", title="Test video")
    video2 = "notVideo"  # type: ignore
    assert not (video1 == video2)
