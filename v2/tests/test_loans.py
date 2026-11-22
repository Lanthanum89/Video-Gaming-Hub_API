import pytest

from conftest import TODAY


def _lend(client, game, customer, **extra):
    return client.post("/loans", json={"game_id": game["id"], "customer_id": customer["id"], **extra})


def test_create_loan_applies_defaults(client, game, customer):
    r = _lend(client, game, customer)
    assert r.status_code == 201
    loan = r.get_json()
    assert loan["loaned_on"] == TODAY.isoformat()
    assert loan["due_on"] == "2026-03-15"  # 14-day default
    assert loan["returned_on"] is None
    assert loan["overdue"] is False
    assert r.headers["Location"] == f"/loans/{loan['id']}"


def test_cannot_lend_a_game_twice(client, game, customer):
    """The core v1 bug: nothing stopped the same copy going out twice."""
    assert _lend(client, game, customer).status_code == 201
    r = _lend(client, game, customer)
    assert r.status_code == 409
    assert len(client.get("/loans?status=active").get_json()) == 1


def test_return_then_lend_again(client, game, customer):
    loan = _lend(client, game, customer).get_json()
    r = client.post(f"/loans/{loan['id']}/return")
    assert r.status_code == 200
    assert r.get_json()["returned_on"] == TODAY.isoformat()
    assert client.get(f"/games/{game['id']}").get_json()["available"] is True
    assert _lend(client, game, customer).status_code == 201


def test_double_return_is_409(client, game, customer):
    loan = _lend(client, game, customer).get_json()
    client.post(f"/loans/{loan['id']}/return")
    assert client.post(f"/loans/{loan['id']}/return").status_code == 409


@pytest.mark.parametrize("missing", ["game_id", "customer_id"])
def test_loan_for_missing_game_or_customer_is_404(client, game, customer, missing):
    body = {"game_id": game["id"], "customer_id": customer["id"], missing: 999}
    assert client.post("/loans", json=body).status_code == 404


@pytest.mark.parametrize(
    "extra, field",
    [
        ({"loaned_on": "2026-03-10", "due_on": "2026-03-20"}, "loaned_on"),  # future
        ({"loaned_on": "2026-02-20", "due_on": "2026-02-10"}, "due_on"),  # due before start
        ({"due_on": "next tuesday"}, "due_on"),  # not a date
    ],
)
def test_loan_date_validation(client, game, customer, extra, field):
    r = _lend(client, game, customer, **extra)
    assert r.status_code == 422
    assert r.get_json()["error"]["details"][0]["field"] == field


def test_wrong_types_are_422_not_500(client):
    """v1 sent these straight to MySQL and returned a 500."""
    r = client.post("/loans", json={"game_id": "banana", "customer_id": None})
    assert r.status_code == 422


def test_return_date_cannot_precede_loan(client, game, customer):
    loan = _lend(client, game, customer, loaned_on="2026-02-20").get_json()
    r = client.post(f"/loans/{loan['id']}/return", json={"returned_on": "2026-02-19"})
    assert r.status_code == 422


def test_status_filters(client, game, customer):
    other = client.post("/games", json={"title": "Garden Ring", "platform": "PS5"}).get_json()
    third = client.post("/games", json={"title": "Wizard School", "platform": "PS5"}).get_json()

    overdue = _lend(client, game, customer, loaned_on="2026-02-01", due_on="2026-02-15").get_json()
    returned = _lend(client, other, customer).get_json()
    client.post(f"/loans/{returned['id']}/return")
    active = _lend(client, third, customer).get_json()

    def ids(status):
        return {l["id"] for l in client.get(f"/loans?status={status}").get_json()}

    assert ids("overdue") == {overdue["id"]}
    assert ids("returned") == {returned["id"]}
    assert ids("active") == {overdue["id"], active["id"]}
    assert client.get(f"/loans/{overdue['id']}").get_json()["overdue"] is True
    assert client.get("/loans?status=lost").status_code == 400
