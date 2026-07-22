"""Pair-frequency based ticket prediction strategy."""

from __future__ import annotations

import random
from typing import Any

import pandas as pd

from core.ticket import Ticket
from features.pair_frequency import calculate
from models.registry import register
from utils.loader import load_lottery

METHOD_NAME = "pair"

NUMBER_COLUMNS = ["N1", "N2", "N3", "N4", "N5"]
NUMBERS_PER_TICKET = 5


def predict(df: pd.DataFrame, total_predictions: int = 20) -> list[Ticket]:
    """Generate candidate tickets from the most frequent number pairs.

    Each candidate ticket is seeded with the two numbers of a frequently
    co-occurring pair (computed via ``features.pair_frequency.calculate``),
    filled out with random remaining numbers, and scored by the seed
    pair's historical co-occurrence count.

    Args:
        df: Historical draw data, as returned by ``utils.loader.load_lottery``.
        total_predictions: Maximum number of tickets to generate. Fewer
            may be returned if the data does not contain enough distinct
            pairs.

    Returns:
        Candidate tickets, ordered by descending seed-pair frequency.
    """
    pair_counts = calculate(df)

    max_number = int(df[NUMBER_COLUMNS].values.max())
    special_max = int(df["SpecialBall"].max())

    tickets = []
    for (a, b), count in pair_counts.most_common(total_predictions):
        pool = [n for n in range(1, max_number + 1) if n not in (a, b)]
        fillers = random.sample(pool, NUMBERS_PER_TICKET - 2)

        numbers = sorted([a, b, *fillers])
        special = random.randint(1, special_max)

        tickets.append(
            Ticket(
                numbers=numbers,
                special=special,
                score=float(count),
                method=METHOD_NAME,
            )
        )

    return tickets


def generate(
    game: str,
    total_predictions: int = 20,
    df: pd.DataFrame | None = None,
) -> list[dict[str, Any]]:
    """Registry entry point: load ``game`` data and predict tickets.

    Args:
        game: Lottery game name understood by ``utils.loader.load_lottery``.
        total_predictions: Maximum number of tickets to generate.
        df: Historical draw data to use instead of loading it via
            ``utils.loader.load_lottery``. Lets callers (e.g. a
            backtesting engine) score against a limited training window.

    Returns:
        Tickets as plain dicts, matching the format the rest of
        ``predict.py`` (CSV/JSON export via ``utils.writer.save_predictions``)
        already expects from the other registered methods.
    """
    if df is None:
        df = load_lottery(game)
    tickets = predict(df, total_predictions)

    return [
        {
            "numbers": ticket.numbers,
            "special": ticket.special,
            "score": ticket.score,
            "method": ticket.method,
        }
        for ticket in tickets
    ]


register(METHOD_NAME, generate)
