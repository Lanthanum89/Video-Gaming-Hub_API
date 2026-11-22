"""HTTP layer: parse the request, call a service, shape the response.

Routes contain no SQL and no try/except. Errors are raised as exceptions and
turned into JSON in one place (errors.py), instead of v1's copy-pasted
try/except in every route.
"""

from datetime import date

from flask import Blueprint, request, url_for

from . import services
from .db import get_session
from .errors import ApiError
from .models import Customer, Game, Loan
from .schemas import CustomerIn, GameIn, LoanIn, ReturnIn

bp = Blueprint("api", __name__)


# --- Helpers ---------------------------------------------------------------

def _json_body(optional: bool = False) -> dict:
    if optional and not request.get_data():
        return {}
    if not request.is_json:
        raise ApiError(415, "unsupported_media_type", "Send a JSON body with Content-Type: application/json")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(400, "bad_request", "Request body must be a valid JSON object")
    return data


def _bool_arg(name: str) -> bool | None:
    raw = request.args.get(name)
    if raw is None:
        return None
    if raw.lower() in ("true", "1"):
        return True
    if raw.lower() in ("false", "0"):
        return False
    raise ApiError(400, "bad_request", f"Query parameter '{name}' must be true or false")


def _created(body: dict, endpoint: str, **ids):
    return body, 201, {"Location": url_for(endpoint, **ids)}


def _game(game: Game, on_loan: bool) -> dict:
    return {
        "id": game.id,
        "title": game.title,
        "platform": game.platform,
        "genre": game.genre,
        "available": not on_loan,
    }


def _customer(customer: Customer) -> dict:
    return {"id": customer.id, "name": customer.name, "email": customer.email}


def _loan(loan: Loan, today: date) -> dict:
    return {
        "id": loan.id,
        "game_id": loan.game_id,
        "customer_id": loan.customer_id,
        "loaned_on": loan.loaned_on.isoformat(),
        "due_on": loan.due_on.isoformat(),
        "returned_on": loan.returned_on.isoformat() if loan.returned_on else None,
        "overdue": loan.returned_on is None and loan.due_on < today,
    }


# --- Routes ----------------------------------------------------------------

@bp.get("/")
def index():
    return {
        "service": "Video Gaming Hub API",
        "version": 2,
        "resources": ["/games", "/customers", "/loans"],
    }


@bp.get("/games")
def list_games():
    rows = services.list_games(get_session(), available=_bool_arg("available"))
    return [_game(g, on_loan) for g, on_loan in rows]


@bp.get("/games/<int:game_id>")
def get_game(game_id: int):
    return _game(*services.get_game(get_session(), game_id))


@bp.post("/games")
def create_game():
    game = services.create_game(get_session(), GameIn.model_validate(_json_body()))
    return _created(_game(game, on_loan=False), "api.get_game", game_id=game.id)


@bp.get("/customers")
def list_customers():
    return [_customer(c) for c in services.list_customers(get_session())]


@bp.get("/customers/<int:customer_id>")
def get_customer(customer_id: int):
    return _customer(services.get_customer(get_session(), customer_id))


@bp.get("/customers/<int:customer_id>/loans")
def list_customer_loans(customer_id: int):
    session = get_session()
    services.get_customer(session, customer_id)  # 404 rather than an empty list
    today = services.today()
    return [_loan(l, today) for l in services.list_loans(session, customer_id=customer_id)]


@bp.post("/customers")
def create_customer():
    customer = services.create_customer(get_session(), CustomerIn.model_validate(_json_body()))
    return _created(_customer(customer), "api.get_customer", customer_id=customer.id)


@bp.delete("/customers/<int:customer_id>")
def delete_customer(customer_id: int):
    services.delete_customer(get_session(), customer_id)
    return "", 204


@bp.get("/loans")
def list_loans():
    status = request.args.get("status")
    if status is not None and status not in services.LOAN_STATUSES:
        raise ApiError(400, "bad_request", f"status must be one of: {', '.join(services.LOAN_STATUSES)}")
    today = services.today()
    return [_loan(l, today) for l in services.list_loans(get_session(), status=status)]


@bp.get("/loans/<int:loan_id>")
def get_loan(loan_id: int):
    return _loan(services.get_loan(get_session(), loan_id), services.today())


@bp.post("/loans")
def create_loan():
    loan = services.create_loan(get_session(), LoanIn.model_validate(_json_body()))
    return _created(_loan(loan, services.today()), "api.get_loan", loan_id=loan.id)


@bp.post("/loans/<int:loan_id>/return")
def return_loan(loan_id: int):
    data = ReturnIn.model_validate(_json_body(optional=True))
    return _loan(services.return_loan(get_session(), loan_id, data), services.today())
