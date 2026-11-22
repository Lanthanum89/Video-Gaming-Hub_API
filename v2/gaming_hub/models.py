"""Database tables.

Key change from v1: there is no `Games.Status` column. Whether a game is on
loan is a fact the loans table already records (an active loan has no
`returned_on`), so storing it twice only creates a way for the two to
disagree, which they did in the v1 seed data.
"""

from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    platform: Mapped[str] = mapped_column(String(50))
    genre: Mapped[str | None] = mapped_column(String(50))

    loans: Mapped[list["Loan"]] = relationship(back_populates="game")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254), unique=True)

    loans: Mapped[list["Loan"]] = relationship(back_populates="customer")


class Loan(Base):
    __tablename__ = "loans"
    __table_args__ = (
        CheckConstraint("due_on >= loaned_on", name="ck_loan_due_after_start"),
        CheckConstraint(
            "returned_on IS NULL OR returned_on >= loaned_on",
            name="ck_loan_returned_after_start",
        ),
        # "Is this game currently out?" is the hottest query in the app.
        Index("ix_loans_game_active", "game_id", "returned_on"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # RESTRICT: loan history is a record of what happened, so deleting a
    # game or customer must not silently delete (or orphan) it.
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="RESTRICT"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"))
    loaned_on: Mapped[date] = mapped_column(Date)
    due_on: Mapped[date] = mapped_column(Date)
    returned_on: Mapped[date | None] = mapped_column(Date)

    game: Mapped[Game] = relationship(back_populates="loans")
    customer: Mapped[Customer] = relationship(back_populates="loans")
