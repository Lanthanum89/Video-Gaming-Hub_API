"""Every failure is JSON with the same shape, including ones Flask raises itself."""


def _assert_json_error(r, status):
    assert r.status_code == status
    assert r.is_json, r.data[:80]
    assert set(r.get_json()["error"]) >= {"code", "message"}


def test_form_body_is_json_415(client):
    # v1 returned Flask's HTML error page here.
    _assert_json_error(client.post("/games", data={"title": "x"}), 415)


def test_malformed_json_is_400(client):
    _assert_json_error(client.post("/games", data="{bad", content_type="application/json"), 400)


def test_json_array_body_is_400(client):
    _assert_json_error(client.post("/games", json=[1, 2]), 400)


def test_unknown_route_is_json_404(client):
    _assert_json_error(client.get("/nope"), 404)


def test_wrong_method_is_json_405(client):
    _assert_json_error(client.put("/games"), 405)


def test_unexpected_error_hides_internals(app, client, monkeypatch):
    from gaming_hub import services

    def boom(*_a, **_k):
        raise RuntimeError("connection to db-prod-01.internal refused")

    monkeypatch.setattr(services, "list_games", boom)
    r = client.get("/games")
    _assert_json_error(r, 500)
    assert "db-prod-01" not in r.get_data(as_text=True)
