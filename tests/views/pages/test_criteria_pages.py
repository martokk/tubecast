from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Cookies
from sqlmodel import Session

from app import crud, models
from app.models import Criteria, Filter, Source
from app.models.criteria import CriteriaBase, CriteriaField, CriteriaOperator, CriteriaUnitOfMeasure
from tests.mock_objects import MOCK_CRITERIA_1, MOCK_CRITERIA_2


def test_view_filter(
    db: Session,  # pylint: disable=unused-argument
    normal_user_cookies: Cookies,
    source_1: Source,
    filter_1: Filter,
    criteria_1: models.Criteria,
    client: TestClient,
) -> None:
    """
    Test view_filter.
    """

    client.cookies = normal_user_cookies
    response = client.get(f"/filter/{filter_1.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/filter/{filter_1.id}"
    assert response.template.name == "filter/view.html"  # type: ignore
    assert response.context["filter"].id == filter_1.id  # type: ignore# type: ignore
    assert response.context["filter"].criterias[0].id == criteria_1.id  # type: ignore
    assert response.context["filter"].criterias[0].field == MOCK_CRITERIA_1["field"]  # type: ignore
    assert response.context["filter"].criterias[0].operator == MOCK_CRITERIA_1["operator"]  # type: ignore
    assert response.context["filter"].criterias[0].value == str(MOCK_CRITERIA_1["value"])  # type: ignore
    assert response.context["filter"].criterias[0].unit_of_measure == MOCK_CRITERIA_1["unit_of_measure"]  # type: ignore


def test_handle_create_criteria(
    db: Session,  # pylint: disable=unused-argument
    normal_user_cookies: Cookies,
    source_1: Source,
    filter_1: Filter,
    criteria_1: models.Criteria,
    client: TestClient,
) -> None:
    """
    Test handle_create_filter.
    """
    client.cookies = normal_user_cookies
    response = client.post(
        f"/filter/{filter_1.id}/criteria/create",
        data=MOCK_CRITERIA_2,
    )
    assert response.status_code == status.HTTP_200_OK
    response_criteria = response.context["filter"].criterias[1]  # type: ignore
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/filter/{response_criteria.filter.id}"
    assert response.template.name == "filter/view.html"  # type: ignore
    assert response_criteria.field == MOCK_CRITERIA_2["field"]
    assert response_criteria.operator == MOCK_CRITERIA_2["operator"]
    assert response_criteria.value == MOCK_CRITERIA_2["value"]
    assert response_criteria.unit_of_measure == MOCK_CRITERIA_2["unit_of_measure"]

    client.cookies = normal_user_cookies
    response = client.post(
        f"/filter/{filter_1.id}/criteria/create",
        data=MOCK_CRITERIA_2,
    )
    assert response.status_code == status.HTTP_200_OK


def test_handle_create_criteria_validation(
    db: Session,  # pylint: disable=unused-argument
    normal_user_cookies: Cookies,
    source_1: Source,
    filter_1: Filter,
    criteria_1: models.Criteria,
    client: TestClient,
) -> None:
    """
    Test handle_create_filter.
    """
    # Test Validation - Field
    invalid_criteria = MOCK_CRITERIA_2.copy()
    invalid_criteria["field"] = "invalid_field"

    response = client.post(
        f"/filter/{filter_1.id}/criteria/create",
        data=invalid_criteria,
    )
    response_criteria = response.context["filter"].criterias[0]  # type: ignore
    assert response.status_code == status.HTTP_200_OK
    assert response.context["alerts"].danger[0] == "Field must be 'released', 'created', 'duration' or 'keyword'"  # type: ignore

    # Test Validation - Operation
    invalid_criteria = MOCK_CRITERIA_2.copy()
    invalid_criteria["operator"] = "invalid"

    response = client.post(
        f"/filter/{filter_1.id}/criteria/create",
        data=invalid_criteria,
    )
    response_criteria = response.context["filter"].criterias[0]  # type: ignore
    assert response.status_code == status.HTTP_200_OK
    assert response.context["alerts"].danger[0] == "Operator for 'keyword' field must be 'must_contain' or 'must_not_contain'"  # type: ignore

    # Test Validation - Operation
    invalid_criteria = MOCK_CRITERIA_2.copy()
    invalid_criteria["unit_of_measure"] = "invalid"

    response = client.post(
        f"/filter/{filter_1.id}/criteria/create",
        data=invalid_criteria,
    )
    response_criteria = response.context["filter"].criterias[0]  # type: ignore
    assert response.status_code == status.HTTP_200_OK
    assert response.context["alerts"].danger[0] == "Unit of measure must be 'keyword'"  # type: ignore

    # Test Validation - Operation
    invalid_criteria = MOCK_CRITERIA_2.copy()
    invalid_criteria["field"] = models.CriteriaField.RELEASED.value
    invalid_criteria["operator"] = "invalid"

    response = client.post(
        f"/filter/{filter_1.id}/criteria/create",
        data=invalid_criteria,
    )
    response_criteria = response.context["filter"].criterias[0]  # type: ignore
    assert response.status_code == status.HTTP_200_OK
    assert response.context["alerts"].danger[0] == "Operator for 'released' and 'created' fields must be 'within'"  # type: ignore

    # Test Validation - Operation
    invalid_criteria = MOCK_CRITERIA_2.copy()
    invalid_criteria["field"] = models.CriteriaField.RELEASED.value
    invalid_criteria["operator"] = models.CriteriaOperator.WITHIN.value
    invalid_criteria["unit_of_measure"] = "invalid"

    response = client.post(
        f"/filter/{filter_1.id}/criteria/create",
        data=invalid_criteria,
    )
    response_criteria = response.context["filter"].criterias[0]  # type: ignore
    assert response.status_code == status.HTTP_200_OK
    assert response.context["alerts"].danger[0] == "Unit of measure must be 'seconds', 'minutes', 'hours', or 'days'"  # type: ignore

    # Test Validation - Operation
    invalid_criteria = MOCK_CRITERIA_2.copy()
    invalid_criteria["field"] = models.CriteriaField.DURATION.value
    invalid_criteria["operator"] = "invalid"

    response = client.post(
        f"/filter/{filter_1.id}/criteria/create",
        data=invalid_criteria,
    )
    response_criteria = response.context["filter"].criterias[0]  # type: ignore
    assert response.status_code == status.HTTP_200_OK
    assert response.context["alerts"].danger[0] == "Operator for 'duration' field must be 'shorter_than' or 'longer_than'"  # type: ignore

    # Test Validation - Value
    invalid_criteria = MOCK_CRITERIA_1.copy()
    invalid_criteria["value"] = "invalid"

    response = client.post(
        f"/filter/{filter_1.id}/criteria/create",
        data=invalid_criteria,
    )
    response_criteria = response.context["filter"].criterias[0]  # type: ignore
    assert response.status_code == status.HTTP_200_OK
    assert response.context["alerts"].danger[0] == "Value must be an integer"  # type: ignore

    # Test Validation - Unit of Measure
    invalid_criteria = MOCK_CRITERIA_1.copy()
    invalid_criteria["unit_of_measure"] = "invalid"

    response = client.post(
        f"/filter/{filter_1.id}/criteria/create",
        data=invalid_criteria,
    )
    response_criteria = response.context["filter"].criterias[0]  # type: ignore
    assert response.status_code == status.HTTP_200_OK
    assert response.context["alerts"].danger[0] == "Unit of measure must be 'seconds', 'minutes', 'hours' or 'days'"  # type: ignore


def test_edit_criteria(
    db: Session,
    client: TestClient,
    normal_user_cookies: Cookies,
    source_1: Source,
    filter_1: Filter,
    criteria_1: models.Criteria,
) -> None:
    """
    Test edit_criteria.
    """

    # Test edit criteria
    client.cookies = normal_user_cookies
    response = client.get(
        f"/filter/{filter_1.id}/criteria/{criteria_1.id}/edit",  # type: ignore
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/filter/{filter_1.id}/criteria/{criteria_1.id}/edit"
    assert response.template.name == "criteria/edit.html"  # type: ignore

    # Test invalid criteria id
    response = client.get(
        f"/filter/{filter_1.id}/criteria/invalid_criteria_id/edit",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/filter/{filter_1.id}"
    assert response.history[0].status_code == status.HTTP_302_FOUND
    assert response.context["alerts"].danger[0] == "Criteria not found"  # type: ignore


def test_handle_edit_criteria(
    db: Session,
    client: TestClient,
    normal_user_cookies: Cookies,
    source_1: Source,
    filter_1: Filter,
    criteria_1: Criteria,
) -> None:
    """
    Test handle_edit_filter.
    """
    MOCK_CRITERIA_UPDATE = MOCK_CRITERIA_2

    # Test edit filter
    client.cookies = normal_user_cookies
    response = client.post(
        f"/filter/{filter_1.id}/criteria/{criteria_1.id}/edit",  # type: ignore
        data=MOCK_CRITERIA_UPDATE,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/filter/{filter_1.id}"
    assert response.template.name == "filter/view.html"  # type: ignore
    assert response.context["filter"].id == filter_1.id  # type: ignore
    assert response.context["filter"].criterias[0].id == criteria_1.id  # type: ignore
    assert response.context["filter"].criterias[0].field == MOCK_CRITERIA_UPDATE["field"]  # type: ignore
    assert response.context["filter"].criterias[0].operator == MOCK_CRITERIA_UPDATE["operator"]  # type: ignore
    assert response.context["filter"].criterias[0].value == MOCK_CRITERIA_UPDATE["value"]  # type: ignore
    assert response.context["filter"].criterias[0].unit_of_measure == MOCK_CRITERIA_UPDATE["unit_of_measure"]  # type: ignore

    # Test invalid filter id
    response = client.post(
        f"/filter/{filter_1.id}/criteria/invalid_criteria_id/edit",  # type: ignore
        data=MOCK_CRITERIA_UPDATE,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/filter/{filter_1.id}"
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.context["alerts"].danger[0] == "Criteria not found"  # type: ignore

    # Test invalid filter id
    response = client.post(
        f"/filter/{filter_1.id}/criteria/invalid_criteria_id/edit",  # type: ignore
        data=MOCK_CRITERIA_UPDATE,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/filter/{filter_1.id}"
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.context["alerts"].danger[0] == "Criteria not found"  # type: ignore

    # Test validation error
    MOCK_CRITERIA_TEMP = MOCK_CRITERIA_1.copy()
    MOCK_CRITERIA_TEMP["value"] = "invalid_field"
    response = client.post(
        f"/filter/{filter_1.id}/criteria/{criteria_1.id}/edit",
        data=MOCK_CRITERIA_TEMP,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.context["alerts"].danger[0] == "Value must be an integer"  # type: ignore


def test_delete_criteria(
    db: Session,
    client: TestClient,
    normal_user_cookies: Cookies,
    source_1: Source,
    filter_1: Filter,
    criteria_1: Criteria,
) -> None:
    """
    Test delete_criteria.
    """

    # Test delete criteria
    client.cookies = normal_user_cookies
    response = client.get(
        f"/filter/{filter_1.id}/criteria/{criteria_1.id}/delete",  # type: ignore
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/filter/{filter_1.id}"
    assert response.template.name == "filter/view.html"  # type: ignore

    # Test criteria not found
    response = client.get(
        f"/filter/{filter_1.id}/criteria/{criteria_1.id}/delete",  # type: ignore
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.url.path == f"/filter/{filter_1.id}"
    assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
    assert response.context["alerts"].danger[0] == "Criteria not found"  # type: ignore

    # Test DeleteError
    with patch("app.crud.criteria.CriteriaCRUD.remove") as mock_delete_criteria:
        mock_delete_criteria.side_effect = crud.DeleteError()
        response = client.get(
            f"/filter/{filter_1.id}/criteria/{criteria_1.id}/delete",  # type: ignore
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.url.path == f"/filter/{filter_1.id}"
        assert response.history[0].status_code == status.HTTP_303_SEE_OTHER
        assert response.context["alerts"].danger[0] == "Error deleting criteria"  # type: ignore


def test_criteria_is_within_timedelta() -> None:
    delta = 5  # days
    unit_of_measure = CriteriaUnitOfMeasure.DAYS.value
    now = datetime.utcnow()
    dt = now - timedelta(days=delta - 1)

    c = Criteria(
        id="test-id",
        field="created",
        operator="within",
        value=str(delta),
        unit_of_measure=unit_of_measure,
    )

    result = c.is_within_timedelta(dt=dt, value=delta, unit_of_measure=unit_of_measure)

    assert result is True


def test_criteria_is_not_within_timedelta() -> None:
    delta = 10 * 60  # 10 minutes
    unit_of_measure = CriteriaUnitOfMeasure.MINUTES.value
    now = datetime.utcnow()
    dt = now - timedelta(minutes=delta + 1)

    c = Criteria(
        id="test-id",
        field="created",
        operator="within",
        value=str(delta),
        unit_of_measure=unit_of_measure,
    )

    result = c.is_within_timedelta(dt=dt, value=delta, unit_of_measure=unit_of_measure)
    assert result is False

    # Test invalid unit of measure
    with pytest.raises(ValueError):
        c.is_within_timedelta(dt=dt, value=delta, unit_of_measure="invalid")


def test_criteria_is_within_duration_shorter_than_value() -> None:
    """
    Tests the Criteria class's ability to correctly determine whether a given video duration
    is shorter than a specified duration value. Validates the handling of:
    - Valid duration checks (expecting True for shorter durations).
    - Handling of invalid unit of measure (expecting ValueError).
    - Handling of invalid comparison operator (expecting ValueError).
    - Behavior when video duration is unspecified (None), where the logic's handling of None
      is tested against a 'shorter than' condition (assuming None behaves like a 0 duration).
    """
    duration = 120  # 2 minutes
    delta = 121  # seconds
    unit_of_measure = CriteriaUnitOfMeasure.SECONDS.value
    operator = CriteriaOperator.SHORTER_THAN.value

    c = Criteria(
        id="test-id",
        field="duration",
        operator=operator,
        value=str(delta),
        unit_of_measure=unit_of_measure,
    )

    result = c.is_within_duration(
        video_duration=duration, operator=operator, value=delta, unit_of_measure=unit_of_measure
    )
    assert result is True

    # Test invalid unit of measure
    with pytest.raises(ValueError):
        c.is_within_duration(
            video_duration=duration, operator=operator, value=delta, unit_of_measure="invalid"
        )

    # Test invalid operator
    with pytest.raises(ValueError):
        c.is_within_duration(
            video_duration=duration,
            operator="invalid",
            value=delta,
            unit_of_measure=unit_of_measure,
        )

    # Test missing duration
    result = c.is_within_duration(
        video_duration=None, operator=operator, value=delta, unit_of_measure=unit_of_measure
    )
    assert result is False


def test_criteria_is_within_duration_longer_than_value() -> None:
    duration = 4 * 60  # 4 minutes
    delta = 3  # minutes
    unit_of_measure = CriteriaUnitOfMeasure.MINUTES.value
    operator = CriteriaOperator.LONGER_THAN.value

    c = Criteria(
        id="test-id",
        field="duration",
        operator=operator,
        value=str(delta),
        unit_of_measure=unit_of_measure,
    )

    result = c.is_within_duration(
        video_duration=duration, operator=operator, value=delta, unit_of_measure=unit_of_measure
    )
    assert result is True

    # Alternate Unit of Measure
    result = c.is_within_duration(
        video_duration=duration,
        operator=operator,
        value=delta,
        unit_of_measure=CriteriaUnitOfMeasure.HOURS.value,
    )
    assert result is False

    # Alternate Unit of Measure
    result = c.is_within_duration(
        video_duration=duration,
        operator=operator,
        value=delta,
        unit_of_measure=CriteriaUnitOfMeasure.DAYS.value,
    )
    assert result is False


def test_criteria_matches_contains_must_contain(source_1_w_videos: Source) -> None:
    video = source_1_w_videos.videos[0]
    keyword = str(video.title).split(" ")[0]
    c = Criteria(
        id="test-id",
        field=CriteriaField.KEYWORD.value,
        operator=CriteriaOperator.MUST_CONTAIN.value,
        value=keyword,
        unit_of_measure=CriteriaUnitOfMeasure.KEYWORD.value,
    )

    result = c.matches_contains(video=video, keyword=keyword)
    assert result is True

    # Test invalid operator
    c.operator = "invalid"
    with pytest.raises(ValueError):
        c.matches_contains(video=video, keyword=keyword)


def test_criteria_matches_contains_must_not_contain(source_1_w_videos: Source) -> None:
    video = source_1_w_videos.videos[0]
    keyword = "cats"
    c = Criteria(
        id="test-id",
        field=CriteriaField.KEYWORD.value,
        operator=CriteriaOperator.MUST_NOT_CONTAIN.value,
        value=keyword,
        unit_of_measure=CriteriaUnitOfMeasure.KEYWORD.value,
    )

    result = c.matches_contains(video=video, keyword=keyword)
    assert result is True


def test_criteria_filter_videos(source_1_w_videos: Source) -> None:
    # Create criteria to filter videos released within the last month
    c = Criteria(
        id="test-id",
        field=CriteriaField.KEYWORD.value,
        operator=CriteriaOperator.MUST_CONTAIN.value,
        value="Bidens",
        unit_of_measure=CriteriaUnitOfMeasure.KEYWORD.value,
    )

    filtered_videos = c.filter_videos(source_1_w_videos.videos)
    assert len(filtered_videos) == 1

    c = Criteria(
        id="test-id",
        field=CriteriaField.KEYWORD.value,
        operator=CriteriaOperator.MUST_CONTAIN.value,
        value="XXXXX",
        unit_of_measure=CriteriaUnitOfMeasure.KEYWORD.value,
    )

    filtered_videos = c.filter_videos(source_1_w_videos.videos)
    assert len(filtered_videos) == 0

    c = Criteria(
        id="test-id",
        field=CriteriaField.KEYWORD.value,
        operator=CriteriaOperator.MUST_NOT_CONTAIN.value,
        value="live",
        unit_of_measure=CriteriaUnitOfMeasure.KEYWORD.value,
    )

    filtered_videos = c.filter_videos(source_1_w_videos.videos)
    assert len(filtered_videos) == 1

    c = Criteria(
        id="test-id",
        field=CriteriaField.CREATED.value,
        operator=CriteriaOperator.WITHIN.value,
        value="1",
        unit_of_measure=CriteriaUnitOfMeasure.DAYS.value,
    )

    filtered_videos = c.filter_videos(source_1_w_videos.videos)
    assert len(filtered_videos) == 2

    c = Criteria(
        id="test-id",
        field=CriteriaField.CREATED.value,
        operator=CriteriaOperator.WITHIN.value,
        value="1",
        unit_of_measure=CriteriaUnitOfMeasure.HOURS.value,
    )

    filtered_videos = c.filter_videos(source_1_w_videos.videos)
    assert len(filtered_videos) == 2

    c = Criteria(
        id="test-id",
        field=CriteriaField.CREATED.value,
        operator=CriteriaOperator.WITHIN.value,
        value="1",
        unit_of_measure=CriteriaUnitOfMeasure.HOURS.value,
    )

    filtered_videos = c.filter_videos(source_1_w_videos.videos)
    assert len(filtered_videos) == 2

    c = Criteria(
        id="test-id",
        field=CriteriaField.RELEASED.value,
        operator=CriteriaOperator.WITHIN.value,
        value="100",
        unit_of_measure=CriteriaUnitOfMeasure.SECONDS.value,
    )

    filtered_videos = c.filter_videos(source_1_w_videos.videos)
    assert len(filtered_videos) == 0
