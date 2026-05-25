import pytest

@pytest.mark.asyncio
async def test_login(async_client):
    resp = await async_client.post("/auth/login", json={"username": "testuser"})
    assert resp.status_code == 200
    assert resp.json() == {"token": "testuser"}

@pytest.mark.asyncio
async def test_create_and_join_game(async_client):
    # Создаём игру
    r = await async_client.post("/lobby/create_game")
    assert r.status_code == 200
    game_id = r.json()["game_id"]
    
    # Присоединяемся
    r2 = await async_client.post("/lobby/join_game", json={
        "game_id": game_id,
        "username": "Alice"
    })
    assert r2.status_code == 200
    assert r2.json()["status"] == "joined"