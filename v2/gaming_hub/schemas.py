"""Request validation.

v1 only checked that keys were present, so `{"game_id": "banana"}` went
straight to MySQL and came back as a 500. Pydantic checks types, lengths and
formats before any database work, and rejects unknown fields so typos like
`"titel"` fail loudly instead of being ignored.
"""

from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, StringConstraints

Text100 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Text50 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
# Deliberately loose: real email validation means sending an email.
Email = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_lower=True, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GameIn(_Strict):
    title: Text100
    platform: Text50
    genre: Text50 | None = None


class CustomerIn(_Strict):
    name: Text100
    email: Email


class LoanIn(_Strict):
    game_id: PositiveInt
    customer_id: PositiveInt
    # Both optional: defaults (today, today + loan period) are applied by the
    # service layer, which knows the app's clock and config.
    loaned_on: date | None = None
    due_on: date | None = None


class ReturnIn(_Strict):
    returned_on: date | None = Field(default=None)
