def test_index_describes_api(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.get_json()["version"] == 2


def test_create_game_returns_resource_and_location(client):
    r = client.post("/games", json={"title": "  Chess Madness ", "platform": "PC"})
    assert r.status_code == 201
    body = r.get_json()
    assert body == {"id": 1, "title": "Chess Madness", "platform": "PC", "genre": None, "available": True}
    assert r.headers["Location"] == "/games/1"


def test_get_game_404(client):
    r = client.get("/games/999")
    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"


def test_create_game_validation(client):
    r = client.post("/games", json={"title": "", "platform": "x" * 51, "titel": "typo"})
    assert r.status_code == 422
    fields = {d["field"] for d in r.get_json()["error"]["details"]}
    assert fields == {"title", "platform", "titel"}


def test_available_filter_follows_loans(client, game, customer):
    other = client.post("/games", json={"title": "Garden Ring", "platform": "PS5"}).get_json()
    client.post("/loans", json={"game_id": game["id"], "customer_id": customer["id"]})

    available = client.get("/games?available=true").get_json()
    on_loan = client.get("/games?available=false").get_json()
    assert [g["id"] for g in available] == [other["id"]]
    assert [g["id"] for g in on_loan] == [game["id"]]
    assert client.get(f"/games/{game['id']}").get_json()["available"] is False


def test_available_filter_rejects_junk(client):
    assert client.get("/games?available=maybe").status_code == 400
