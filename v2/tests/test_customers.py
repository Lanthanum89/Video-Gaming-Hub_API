def test_create_and_fetch_customer(client):
    r = client.post("/customers", json={"name": "Jack Pearce", "email": "Jack@Example.com"})
    assert r.status_code == 201
    customer = r.get_json()
    assert customer["email"] == "jack@example.com"  # normalised

    # v1 bug: this query used a column called `id` that did not exist, so it always 500'd.
    r = client.get(f"/customers/{customer['id']}")
    assert r.status_code == 200
    assert r.get_json() == customer


def test_duplicate_email_is_409_not_500(client, customer):
    r = client.post("/customers", json={"name": "Someone Else", "email": "AMELIA@example.com"})
    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "conflict"


def test_invalid_email(client):
    r = client.post("/customers", json={"name": "No At", "email": "not-an-email"})
    assert r.status_code == 422


def test_delete_customer(client, customer):
    r = client.delete(f"/customers/{customer['id']}")
    assert r.status_code == 204
    assert client.get(f"/customers/{customer['id']}").status_code == 404


def test_delete_missing_customer_is_404(client):
    assert client.delete("/customers/999").status_code == 404


def test_cannot_delete_customer_with_loan_history(client, game, customer):
    loan = client.post("/loans", json={"game_id": game["id"], "customer_id": customer["id"]}).get_json()
    client.post(f"/loans/{loan['id']}/return")

    r = client.delete(f"/customers/{customer['id']}")
    assert r.status_code == 409
    assert client.get(f"/customers/{customer['id']}").status_code == 200


def test_customer_loans(client, game, customer):
    client.post("/loans", json={"game_id": game["id"], "customer_id": customer["id"]})
    loans = client.get(f"/customers/{customer['id']}/loans").get_json()
    assert len(loans) == 1
    assert client.get("/customers/999/loans").status_code == 404
