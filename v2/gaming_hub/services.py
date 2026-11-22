"""Business rules, kept separate from HTTP.

v1 had no rules at all: a game could be lent twice, lent while "Borrowed",
or lent with a due date before the loan date, and there was no way to return
it. The rules live here so they are enforced the same way whatever calls them
(an HTTP route, a CLI command, a test).
"""

from datetime import date, timedelta

from flask import current_app
from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .errors import ApiError, Conflict, NotFound
from .models import Customer, Game, Loan
from .schemas import CustomerIn, GameIn, LoanIn, ReturnIn


def today() -> date:
    return current_app.config["TODAY"]()


def _invalid(field: str, message: str) -> ApiError:
    return ApiError(422, "validation_error", "Request body failed validation", [{"field": field, "message": message}])


# A correlated subquery: "does this game have a loan with no return date?"
_on_loan = exists().where(Loan.game_id == Game.id, Loan.returned_on.is_(None)).label("on_loan")


# --- Games -----------------------------------------------------------------

def list_games(session: Session, available: bool | None = None) -> list[tuple[Game, bool]]:
    stmt = select(Game, _on_loan).order_by(Game.title)
    if available is True:
        stmt = stmt.where(~_on_loan)
    elif available is False:
        stmt = stmt.where(_on_loan)
    return [(game, on_loan) for game, on_loan in session.execute(stmt)]


def get_game(session: Session, game_id: int) -> tuple[Game, bool]:
    row = session.execute(select(Game, _on_loan).where(Game.id == game_id)).first()
    if row is None:
        raise NotFound("Game", game_id)
    return row[0], row[1]


def create_game(session: Session, data: GameIn) -> Game:
    game = Game(**data.model_dump())
    session.add(game)
    session.commit()
    return game


# --- Customers -------------------------------------------------------------

def list_customers(session: Session) -> list[Customer]:
    return list(session.scalars(select(Customer).order_by(Customer.name)))


def get_customer(session: Session, customer_id: int) -> Customer:
    customer = session.get(Customer, customer_id)
    if customer is None:
        raise NotFound("Customer", customer_id)
    return customer


def create_customer(session: Session, data: CustomerIn) -> Customer:
    customer = Customer(**data.model_dump())
    session.add(customer)
    try:
        session.commit()
    except IntegrityError:
        # Rely on the UNIQUE constraint rather than check-then-insert, which
        # has a race between the check and the insert.
        session.rollback()
        raise Conflict(f"A customer with email {data.email} already exists")
    return customer


def delete_customer(session: Session, customer_id: int) -> None:
    customer = get_customer(session, customer_id)
    if session.scalar(select(exists().where(Loan.customer_id == customer_id))):
        raise Conflict(f"Customer {customer_id} has loan history and cannot be deleted")
    session.delete(customer)
    session.commit()


# --- Loans -----------------------------------------------------------------

LOAN_STATUSES = ("active", "returned", "overdue")


def list_loans(session: Session, status: str | None = None, customer_id: int | None = None) -> list[Loan]:
    stmt = select(Loan).order_by(Loan.loaned_on.desc(), Loan.id.desc())
    if customer_id is not None:
        stmt = stmt.where(Loan.customer_id == customer_id)
    if status == "active":
        stmt = stmt.where(Loan.returned_on.is_(None))
    elif status == "returned":
        stmt = stmt.where(Loan.returned_on.is_not(None))
    elif status == "overdue":
        stmt = stmt.where(Loan.returned_on.is_(None), Loan.due_on < today())
    return list(session.scalars(stmt))


def get_loan(session: Session, loan_id: int, lock: bool = False) -> Loan:
    loan = session.get(Loan, loan_id, with_for_update=lock)
    if loan is None:
        raise NotFound("Loan", loan_id)
    return loan


def create_loan(session: Session, data: LoanIn) -> Loan:
    # Lock the game row so two simultaneous requests cannot both see it as
    # available and both lend it. (MySQL/Postgres honour FOR UPDATE; SQLite
    # ignores it, which is acceptable for a local single-user database.)
    game = session.get(Game, data.game_id, with_for_update=True)
    if game is None:
        raise NotFound("Game", data.game_id)
    get_customer(session, data.customer_id)

    loaned_on = data.loaned_on or today()
    due_on = data.due_on or loaned_on + timedelta(days=current_app.config["LOAN_PERIOD_DAYS"])
    if loaned_on > today():
        raise _invalid("loaned_on", "cannot be in the future")
    if due_on < loaned_on:
        raise _invalid("due_on", "must be on or after loaned_on")

    active = session.scalar(select(Loan.id).where(Loan.game_id == game.id, Loan.returned_on.is_(None)))
    if active is not None:
        raise Conflict(f"Game {game.id} is already on loan (loan {active})")

    loan = Loan(game_id=game.id, customer_id=data.customer_id, loaned_on=loaned_on, due_on=due_on)
    session.add(loan)
    session.commit()
    return loan


def return_loan(session: Session, loan_id: int, data: ReturnIn) -> Loan:
    loan = get_loan(session, loan_id, lock=True)
    if loan.returned_on is not None:
        raise Conflict(f"Loan {loan_id} was already returned on {loan.returned_on.isoformat()}")

    returned_on = data.returned_on or today()
    if returned_on < loan.loaned_on:
        raise _invalid("returned_on", "must be on or after the loan date")
    if returned_on > today():
        raise _invalid("returned_on", "cannot be in the future")

    loan.returned_on = returned_on
    session.commit()
    return loan
