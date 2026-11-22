"""Walk through a typical day at the lending desk against a running API.

    flask --app gaming_hub run          # in one terminal
    python client.py                    # in another

v1's client returned `({"error": ...}, 500)` tuples (a Flask return shape,
meaningless in a client), threw away every response, and printed nothing a
person could follow. This prints what happened and why at each step.
"""

import os
import sys

import requests

BASE_URL = os.environ.get("API_URL", "http://localhost:5000")


def call(method: str, path: str, **kwargs):
    try:
        r = requests.request(method, BASE_URL + path, timeout=5, **kwargs)
    except requests.ConnectionError:
        sys.exit(f"Cannot reach {BASE_URL}. Is the server running? (flask --app gaming_hub run)")
    body = r.json() if r.content else None
    if not r.ok:
        err = body["error"]
        print(f"  -> {r.status_code} {err['code']}: {err['message']}")
        for d in err.get("details", []):
            print(f"       {d['field']}: {d['message']}")
    return r.status_code, body


def main() -> None:
    print("Available games:")
    _, games = call("GET", "/games", params={"available": "true"})
    for g in games:
        print(f"  [{g['id']}] {g['title']} ({g['platform']})")
    if not games:
        sys.exit("Nothing available to lend. Run: flask --app gaming_hub init-db --reset --seed")

    print("\nRegistering a customer:")
    status, customer = call("POST", "/customers", json={"name": "Richard Smith", "email": "richard.sm@example.com"})
    if status == 409:
        print("  (already registered from a previous run, looking them up)")
        _, everyone = call("GET", "/customers")
        customer = next(c for c in everyone if c["email"] == "richard.sm@example.com")
    print(f"  {customer['name']} is customer {customer['id']}")

    game = games[0]
    print(f"\nLending '{game['title']}':")
    _, loan = call("POST", "/loans", json={"game_id": game["id"], "customer_id": customer["id"]})
    print(f"  Loan {loan['id']} created, due back {loan['due_on']}")

    print("\nTrying to lend the same copy again (should be refused):")
    call("POST", "/loans", json={"game_id": game["id"], "customer_id": customer["id"]})

    print("\nOverdue loans:")
    _, overdue = call("GET", "/loans", params={"status": "overdue"})
    for l in overdue:
        print(f"  Loan {l['id']}: game {l['game_id']}, customer {l['customer_id']}, due {l['due_on']}")
    if not overdue:
        print("  None")

    print(f"\nReturning loan {loan['id']}:")
    _, returned = call("POST", f"/loans/{loan['id']}/return")
    print(f"  Returned on {returned['returned_on']}")

    print("\nSending a bad request on purpose (validation errors):")
    call("POST", "/loans", json={"game_id": "banana", "due_on": "next tuesday"})


if __name__ == "__main__":
    main()
