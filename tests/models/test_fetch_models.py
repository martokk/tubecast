import pytest

from tubecast import models


def test_sum_FetchResults() -> None:
    """
    Test adding two FetchResults together.
    """
    results1 = models.FetchResults(sources=1, added_videos=2, deleted_videos=3, refreshed_videos=4)
    results2 = models.FetchResults(sources=5, added_videos=6, deleted_videos=7, refreshed_videos=8)
    results3 = results1 + results2
    assert results3.sources == 6
    assert results3.added_videos == 8
    assert results3.deleted_videos == 10
    assert results3.refreshed_videos == 12

    # Test adding a FetchResults and a non-FetchResults
    wrong_type_result = "test"
    with pytest.raises(TypeError):
        _ = results1 + wrong_type_result
