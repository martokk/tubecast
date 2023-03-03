from fastapi.testclient import TestClient
from httpx import Cookies
from sqlmodel import Session


def test_root_index_authenticated(
    db_with_user: Session,  # pylint: disable=unused-argument
    client: TestClient,
    normal_user_cookies: Cookies,
) -> None:
    """
    Test root index authenticated
    """
    client.cookies = normal_user_cookies
    response = client.get("/")
    assert response.status_code == 200
    assert response.template.name == "source/list.html"  # type: ignore


def test_root_index_unauthenticated(
    db_with_user: Session, client: TestClient  # pylint: disable=unused-argument
) -> None:
    """
    Test root index unauthenticated
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.template.name == "login/login.html"  # type: ignore
