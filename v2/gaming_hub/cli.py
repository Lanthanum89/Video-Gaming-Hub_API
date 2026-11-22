"""`flask --app gaming_hub init-db [--seed] [--reset]`

Replaces v1's hand-run SQL script. Seed dates are relative to today, so the
demo always has a mix of active, overdue and returned loans.
"""

from datetime import timedelta

import click
from flask import Flask

from . import db
from .models import Customer, Game, Loan
from .services import today


def register(app: Flask) -> None:
    @app.cli.command("init-db")
    @click.option("--seed", is_flag=True, help="Insert demo data.")
    @click.option("--reset", is_flag=True, help="Drop all tables first. Destroys data.")
    def init_db(seed: bool, reset: bool) -> None:
        if reset:
            db.drop_schema(app)
        db.create_schema(app)
        click.echo("Schema ready.")
        if seed:
            _seed()
            click.echo("Demo data inserted.")


def _seed() -> None:
    session = db.get_session()
    if session.query(Game).first() is not None:
        raise click.ClickException("Database already has data. Use --reset to start again.")

    games = [
        Game(title="The Legend of Pillars", platform="Nintendo Switch", genre="Action-Adventure"),
        Game(title="Garden Ring", platform="PlayStation 5", genre="Action RPG"),
        Game(title="The Simulations", platform="PC", genre="Simulation"),
        Game(title="Galaxyfield", platform="Xbox Series X", genre="RPG"),
        Game(title="Cybergoth 3077", platform="PlayStation 5", genre="Action RPG"),
        Game(title="Wizard School Legacy", platform="PlayStation 5", genre="Action RPG"),
        Game(title="Chess Madness", platform="PC", genre="Strategy"),
    ]
    customers = [
        Customer(name="Laura Smith", email="lauras@example.com"),
        Customer(name="Amelia Barker", email="ameliab@example.com"),
        Customer(name="Freddie Creese", email="freddiec@example.com"),
        Customer(name="Jack Pearce", email="jackp@example.com"),
    ]
    session.add_all(games + customers)
    session.flush()  # assigns ids

    t = today()
    d = timedelta
    session.add_all([
        Loan(game=games[0], customer=customers[0], loaned_on=t - d(5), due_on=t + d(9)),
        Loan(game=games[3], customer=customers[3], loaned_on=t - d(2), due_on=t + d(12)),
        Loan(game=games[4], customer=customers[0], loaned_on=t - d(10), due_on=t + d(4)),
        Loan(game=games[2], customer=customers[1], loaned_on=t - d(20), due_on=t - d(6)),  # overdue
        Loan(game=games[6], customer=customers[2], loaned_on=t - d(30), due_on=t - d(16), returned_on=t - d(18)),
    ])
    session.commit()
