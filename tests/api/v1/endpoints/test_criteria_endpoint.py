from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import settings
from app.models import Criteria, CriteriaField, CriteriaOperator, CriteriaUnitOfMeasure, Filter


def test_create_criteria(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    filter_1: Filter,
) -> None:
    """
    Test that a normal user can create a source from a URL.
    """
    new_criteria = {
        "field": CriteriaField.DURATION.value,
        "operator": CriteriaOperator.SHORTER_THAN.value,
        "value": 100,
        "unit_of_measure": CriteriaUnitOfMeasure.HOURS.value,
    }

    response = client.post(
        f"{settings.API_V1_PREFIX}/filter/{filter_1.id}/criteria",
        headers=normal_user_token_headers,
        json=new_criteria,
    )
    assert response.status_code == status.HTTP_201_CREATED
    result = response.json()
    assert result["field"] == new_criteria["field"]
    assert result["operator"] == new_criteria["operator"]
    assert result["value"] == str(new_criteria["value"])
    assert result["unit_of_measure"] == new_criteria["unit_of_measure"]
    assert result["filter_id"] == filter_1.id


def test_read_criteria(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
    filter_1: Filter,
    criteria_1: Criteria,
) -> None:
    """
    Test that a superuser can read an source.
    """
    response = client.get(
        f"{settings.API_V1_PREFIX}/criteria/{criteria_1.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    assert result["filter_id"] == criteria_1.filter.id
    assert result["field"] == criteria_1.field
    assert result["operator"] == criteria_1.operator
    assert result["value"] == str(criteria_1.value)
    assert result["unit_of_measure"] == criteria_1.unit_of_measure

    # Test not found for normal user
    response = client.get(
        f"{settings.API_V1_PREFIX}/criteria/invalid_id",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test not found for superuser
    response = client.get(
        f"{settings.API_V1_PREFIX}/criteria/invalid_id",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_criteria(
    db: Session,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
    filter_1: Filter,
    criteria_1: Criteria,
    client: TestClient,
) -> None:
    """
    Test that a normal user can update a criteria.
    """

    # Update all fields
    updated_criteria = {
        "field": CriteriaField.CREATED.value,
        "operator": CriteriaOperator.WITHIN.value,
        "value": 10,
        "unit_of_measure": CriteriaUnitOfMeasure.DAYS.value,
    }

    response = client.patch(
        f"{settings.API_V1_PREFIX}/criteria/{criteria_1.id}",
        headers=normal_user_token_headers,
        json=updated_criteria,
    )

    assert response.status_code == status.HTTP_200_OK

    result = response.json()
    assert result["filter_id"] == filter_1.id
    assert result["field"] == updated_criteria["field"]
    assert result["operator"] == updated_criteria["operator"]
    assert result["value"] == str(updated_criteria["value"])
    assert result["unit_of_measure"] == updated_criteria["unit_of_measure"]

    # Test if obj_in.value is not a int
    updated_criteria["value"] = "invalid_value"
    response = client.patch(
        f"{settings.API_V1_PREFIX}/criteria/{criteria_1.id}",
        headers=normal_user_token_headers,
        json=updated_criteria,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Value must be an integer"

    # Test not found for normal user
    response = client.patch(
        f"{settings.API_V1_PREFIX}/criteria/invalid_id",
        headers=normal_user_token_headers,
        json=updated_criteria,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test not found for superuser
    response = client.patch(
        f"{settings.API_V1_PREFIX}/criteria/invalid_id",
        headers=superuser_token_headers,
        json=updated_criteria,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_criteria(
    db: Session,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
    criteria_1: Criteria,
    client: TestClient,
) -> None:
    """
    Test that a normal user can delete a criteria.
    """
    response = client.delete(
        f"{settings.API_V1_PREFIX}/criteria/{criteria_1.id}",
        headers=normal_user_token_headers,
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Make sure the criteria was deleted
    response = client.get(
        f"{settings.API_V1_PREFIX}/criteria/{criteria_1.id}",
        headers=superuser_token_headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Test not found for normal user
    response = client.delete(
        f"{settings.API_V1_PREFIX}/criteria/invalid_id",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test not found for superuser
    response = client.delete(
        f"{settings.API_V1_PREFIX}/criteria/invalid_id",
        headers=superuser_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
