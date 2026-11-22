# Video Gaming Hub API, v2

A rewrite of the original lending-desk API in the repo root, about 18 months on. Same idea, same stack (Python, Flask, SQL), done properly.

**Read [RETROSPECTIVE.md](RETROSPECTIVE.md)** for what was wrong with v1 and why each change was made.

## Quick start

Needs Python 3.10+. Uses SQLite by default, so there's no database to install.

```sh
cd v2
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

flask --app gaming_hub init-db --seed
flask --app gaming_hub run --debug
```

In a second terminal:

```sh
python client.py     # walks through lending, a refused double-loan, a return and a validation error
pytest               # 31 tests, no server or database needed
```

### Using MySQL instead

```sh
pip install mysql-connector-python
export DATABASE_URL="mysql+mysqlconnector://USER:PASSWORD@localhost/video_gaming_hub"
# PowerShell: $env:DATABASE_URL = "mysql+mysqlconnector://..."
flask --app gaming_hub init-db --seed
```

Create the empty database first (`CREATE DATABASE video_gaming_hub;`). Tables are created by `init-db`. See `.env.example` for all settings. Credentials never go in the repo.

`init-db --reset` drops and recreates every table. It destroys data.

## Data model

```text
games       id, title, platform, genre
customers   id, name, email (unique)
loans       id, game_id -> games, customer_id -> customers,
            loaned_on, due_on (>= loaned_on), returned_on (NULL while out)
```

There's no "status" column on games. A game is available when it has no loan with `returned_on` empty. See retrospective §1.3.

## Endpoints

All requests and responses are JSON. Dates are `YYYY-MM-DD`.

| Method | Path | Notes |
|---|---|---|
| GET | `/` | Service info |
| GET | `/games` | `?available=true\|false` to filter |
| GET | `/games/<id>` | Includes `available` |
| POST | `/games` | `{title, platform, genre?}` → 201 + `Location` |
| GET | `/customers` | |
| GET | `/customers/<id>` | |
| GET | `/customers/<id>/loans` | Loan history for one customer |
| POST | `/customers` | `{name, email}` → 201, 409 if email exists |
| DELETE | `/customers/<id>` | 204, 409 if they have loan history |
| GET | `/loans` | `?status=active\|returned\|overdue` |
| GET | `/loans/<id>` | Includes computed `overdue` |
| POST | `/loans` | `{game_id, customer_id, loaned_on?, due_on?}` |
| POST | `/loans/<id>/return` | Optional `{returned_on}`, defaults to today |

`POST /loans` defaults `loaned_on` to today and `due_on` to 14 days later (`LOAN_PERIOD_DAYS`). It returns 409 if the game is already out.

### Errors

Every error, including 404s for unknown URLs and 405s, has the same shape:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request body failed validation",
    "details": [{ "field": "due_on", "message": "must be on or after loaned_on" }]
  }
}
```

| Status | When |
|---|---|
| 400 | Malformed JSON, bad query parameter |
| 404 | Resource doesn't exist |
| 409 | Breaks a business rule (already on loan, duplicate email, already returned) |
| 415 | Body isn't JSON |
| 422 | JSON is valid but the values aren't |
| 500 | Our fault. Details are logged, not returned |

## Layout

```text
gaming_hub/
  __init__.py   app factory
  config.py     settings from environment variables
  db.py         engine + one session per request, always closed
  models.py     tables and constraints
  schemas.py    request validation (Pydantic)
  services.py   business rules, no HTTP
  api.py        routes: parse, call service, shape response
  errors.py     one JSON error format for everything
  cli.py        init-db / seed command
tests/          pytest, fresh SQLite DB per test
client.py       demo script against a running server
```
