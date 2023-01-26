from fastapi.testclient import TestClient


def test_get_rss_not_found(client: TestClient) -> None:
    response = client.get("/feed/non_existent_source")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"
