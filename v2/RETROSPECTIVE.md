# Retrospective: v1 (mid 2025) vs v2 (late 2026)

v1 was a Code First Girls assignment, written about 18 months before v2. It met the brief and was marked as a learning exercise. Reading it again with more experience, the problems fall into three groups: things that were **actually broken**, things that **worked by luck or not at all under real use**, and **habits** that would hurt on a bigger project.

The v1 code is left untouched in the repo root so the comparison stays honest.

## TL;DR

| | v1 | v2 |
|---|---|---|
| `GET` / `DELETE /customers/<id>` | Always 500 (queried a column that doesn't exist) | Works, 404 when missing |
| Lending the same game twice | Allowed | 409 Conflict |
| Returning a game | Impossible, no endpoint | `POST /loans/<id>/return` |
| Game availability | Stored separately, already out of sync in seed data | Derived from loans, can't drift |
| Bad input (`"game_id": "banana"`) | Sent to MySQL, 500 | 422 with per-field messages |
| Error responses | Mix of JSON and HTML, leaked DB host names | Always JSON, one shape, internals hidden |
| Seed script | Only 1 of 4 loans inserted (syntax error) | CLI seed, consistent data |
| Tests | 4 smoke checks needing live server + MySQL | 31 isolated pytest tests, run in CI |
| Setup | Install MySQL, run SQL by hand, edit committed config | `pip install`, one command, SQLite by default |

---

## 1. Bugs: things that were broken

### 1.1 Two of the nine endpoints could never work

`db_utils.py:111` and `db_utils.py:124`:

```python
cursor.execute("SELECT * FROM Customers WHERE id = %s", (customer_id,))
```

The column is `Customer_id` (`video_gaming_hub_API_schema.sql`), not `id`. MySQL raises `Unknown column 'id'`, which was caught as `DbConnectionError` and returned as a 500. So `GET /customers/<id>` and `DELETE /customers/<id>` failed on every call.

**Why it slipped through:** the tests in `Complementary_Files/testing.py` only covered the four list endpoints. The two broken routes were exactly the untested ones. That's the most useful lesson in this whole file.

### 1.2 The seed script only inserted one loan

`video_gaming_hub_API_schema.sql:51` ends the `INSERT` with `;` after the first row. The next three rows are then standalone `(4, 4, ...);` statements, which are syntax errors. Only Laura Smith's loan was ever inserted.

### 1.3 The data contradicted itself from day one

`Games.Status` was a free-text column maintained by hand, separately from `Game_Loans`. In the seed data:

- Games 1 and 5 were marked `Available` while on loan.
- Game 7 was marked `Borrowed` with no loan at all.

And `POST /loans` never updated it, so it drifted further with every request. The comment on `video_gaming_hub_API_schema.sql:11` shows I knew this was wrong at the time:

> I couldn't get it to sync with the loan table, but this would be ideal, especially if it could update with the loan table automatically

**The fix wasn't syncing it better, it was deleting it.** A game is on loan if it has a loan with no return date. That's a fact the loans table already holds. Storing it twice just creates a second source of truth that can disagree with the first. v2 works it out with a subquery every time (`services.py`, `_on_loan`), so it can't be wrong.

General rule: if a value can be derived from data you already store, derive it. Only denormalise when you've measured a performance problem, and then you need something (a trigger, a transaction) that keeps both copies in step.

### 1.4 The lending rules didn't exist

`POST /loans` would happily:

- lend a game that was already lent out, any number of times
- lend a game that didn't exist, or to a customer who didn't exist (500 from the FK constraint)
- accept a due date before the loan date

And there was no way to return a game, so `Returned_Date` could never be set. For a loan system, that's the main workflow missing.

v2 enforces these rules in `services.py`. Lending locks the game row (`SELECT ... FOR UPDATE`) before checking availability, so two simultaneous requests can't both succeed.

### 1.5 Connection leaks

Every `db_utils` function did:

```python
conn = get_db_connection()
cursor.execute(...)   # if this raises...
conn.close()          # ...this never runs
```

Any exception leaked a connection. `delete_customer_by_id` leaked one even on a *normal* not-found case, because it raised `ValueError` before reaching `conn.close()` (`db_utils.py:113`). Under load MySQL eventually refuses new connections.

v2 opens one session per request and closes it in a Flask teardown hook, which runs whether the request succeeded or not (`db.py`).

---

## 2. Things that "worked" but weren't right

### 2.1 Validation was presence-only

```python
if not all(field in loan_data for field in required_fields):
```

This checks the keys exist, not that the values make sense. Verified against v1 with Flask's test client:

```text
POST /loans {"game_id": "banana", "customer_id": null, "date_of_loan": "tomorrow", ...}
-> 500 {"error": "Database connection failed: ..."}
```

Bad input is the client's fault and should be a 4xx. A 500 tells the client "our fault, try again later", which is wrong and would set off alerts in a real system. v2 validates with Pydantic and returns 422 with a message per field. It also rejects unknown fields, so a typo like `"titel"` fails instead of being silently ignored.

### 2.2 Errors leaked internals and weren't consistent

- `str(err)` from MySQL was returned to the client. Running v1 with no database returns the configured **host name** in the response body. In production that hands an attacker your infrastructure layout.
- Everything database-related was called `DbConnectionError`, including bad SQL and constraint violations. The name lied, which makes debugging harder.
- Sending a form instead of JSON returned Flask's **HTML** 415 page, because only 400/404/500 had JSON handlers. A JSON API that sometimes returns HTML breaks every client that calls `.json()` on the response.
- Duplicate email on `POST /customers` was a 500. It should be a 409 Conflict.

v2 has one error shape for everything (`errors.py`), logs the real exception server-side, and gives the client a generic message.

### 2.3 Inconsistent API contract

- `POST /games` took lowercase `title`, `genre`. `GET /games` returned `Title`, `Genre`, `Game_id` (straight from `SELECT *`). Clients had to know two naming schemes.
- `POST` endpoints returned `{"message": "Game inserted successfully!"}`, not the created record, so the client couldn't learn the new ID without listing everything.
- `/available_games` was a separate endpoint rather than a filter on `/games`.

v2 uses snake_case throughout, returns the created resource with a `Location` header, and uses query parameters for filters (`/games?available=true`, `/loans?status=overdue`).

### 2.4 Deleting a customer would have destroyed history

Even if 1.1 had been fixed, deleting a customer with loans would hit the foreign key and 500. The right response is a 409 explaining why. Loan history is a record of what happened, so v2 refuses to delete customers who have any (`ondelete="RESTRICT"`).

---

## 3. Habits

### 3.1 Security

- **`app.run(debug=True)`** (`main.py:145`) hard-coded. Flask's debugger lets anyone who can trigger an error run Python on the server. It must never be reachable outside your own machine. v2 never sets it in code: use `flask run --debug` locally.
- **`config.py` committed** with a comment saying to create a file called `config.py` with real credentials. That's the same filename, so the real one is one `git add .` away from being public. v2 reads environment variables and git-ignores `.env`.

### 3.2 Repo hygiene

- `.gitignore` listed **itself**, and didn't ignore `__pycache__/` or `config.py`. That's why `__pycache__/*.pyc` files are committed in the root.
- No `requirements.txt`: dependencies were only listed in comments and the README.
- `from config import ...` inside a function (`db_utils.py:9`), hiding a dependency that should be visible at the top of the file.

### 3.3 Testing

`Complementary_Files/testing.py`:

- Ran its tests at import time (`testing.py:38`), not through a test runner, so the first failure stopped everything and nothing was reported.
- Needed the server running *and* a MySQL database with specific seed data.
- Only checked list endpoints returned *something*.

v2 tests use pytest and Flask's test client with a fresh SQLite database per test and a fixed "today", so they're isolated and repeatable. They run in GitHub Actions on every push. Several tests are named after the v1 bug they would have caught.

### 3.4 Copy-paste

Every route repeated the same `try/except DbConnectionError` block, *and* there was a global handler for `DbConnectionError`, so the route-level ones did nothing. Every `db_utils` function repeated the connect/cursor/close boilerplate. In v2, routes raise exceptions and one handler turns them into responses, and the session lifecycle is written once.

### 3.5 Client

`client.py` returned `({"error": ...}, 500)` tuples. That's the shape a *Flask route* returns, copied into a client where it means nothing. The return values were then thrown away, so running it printed "Fetching..." and nothing else. Running it twice also crashed on the duplicate email. v2's `client.py` walks through a real lending-desk scenario, shows each result and error, and is safe to re-run.

---

## 4. What v2 deliberately doesn't do

Scaled to the project, not to an imaginary enterprise:

- **No authentication.** A real lending desk needs it. It's a separate concern and would double the size of this.
- **No pagination.** Fine at this size. First thing to add if lists grow past a few hundred rows.
- **No migrations tool.** `create_all()` is enough until the schema has to change with live data in it. Then use Alembic.
- **No ORM-free raw SQL.** v1 used hand-written SQL, which was a good way to learn. v2 uses SQLAlchemy mainly so the same code runs on SQLite (tests, local) and MySQL (as in v1). The trade-off: one more thing to learn, and the SQL is less visible. The queries in `services.py` are still explicit `select()` statements rather than hidden behind magic.
- **Kept Python and Flask.** Rewriting in TypeScript would show different knowledge, not better knowledge of the same problem. Same stack makes the comparison fair.

## 5. If I did it again from scratch

1. Write the rules first ("a game can only be on one active loan"), then the schema that makes them easy to enforce.
2. Write a test for every endpoint before calling it done. The two endpoints without tests were the two that didn't work.
3. Decide the error format on day one.
4. Never store what you can derive.
