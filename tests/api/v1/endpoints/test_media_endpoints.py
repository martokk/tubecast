from fastapi.testclient import TestClient


async def test_handle_media_404(client: TestClient) -> None:
    response = client.get("/media/wrong-id")
    assert response.status_code == 404
