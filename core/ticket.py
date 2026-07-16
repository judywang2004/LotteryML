"""Data model for a single lottery ticket prediction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class Ticket:
    """A predicted lottery ticket.

    Attributes:
        numbers: The main numbers picked for the ticket.
        special: The special number (e.g. Powerball/Mega Ball).
        score: A numeric score indicating how the ticket ranks
            relative to others produced by the same method.
        method: Name of the prediction method that produced the ticket.
        draw_date: The draw date this ticket is intended for, if known.
    """

    numbers: list[int]
    special: int
    score: float
    method: str
    draw_date: date | None = None
