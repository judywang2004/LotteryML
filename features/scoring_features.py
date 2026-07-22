"""Named, explainable Feature definitions for the ScoringEngine.

Builds the concrete features used to explain why a candidate ticket
scored the way it did: pair co-occurrence, individual number
"hotness", and odd/even balance. Reuses existing calculations
(``features.pair_frequency.calculate``, ``utils.statistics.number_frequency``)
rather than duplicating them.
"""

from __future__ import annotations

from itertools import combinations

import pandas as pd

from core.feature_score import Feature
from core.ticket import Ticket
from features.pair_frequency import calculate as calculate_pair_frequency
from utils.statistics import number_frequency


def build_pair_score_feature(
    df: pd.DataFrame, numbers_count: int = 5, weight: float = 1.0
) -> Feature:
    """Build a feature scoring tickets by historical pair co-occurrence.

    Args:
        df: Historical draw data, as returned by ``utils.loader.load_lottery``.
        numbers_count: How many main numbers each ticket has.
        weight: Weight applied to this feature's normalized value.

    Returns:
        A ``Feature`` named ``"pair"`` (rendered as the ``PairScore``
        output column).
    """
    pair_counts = calculate_pair_frequency(df)
    max_pair_count = max(pair_counts.values(), default=1)
    pairs_per_ticket = max(len(list(combinations(range(numbers_count), 2))), 1)
    max_raw = max_pair_count * pairs_per_ticket

    def extractor(ticket: Ticket) -> float:
        return float(
            sum(
                pair_counts.get(pair, 0)
                for pair in combinations(sorted(ticket.numbers), 2)
            )
        )

    def normalizer(raw_value: float) -> float:
        return raw_value / max_raw if max_raw else 0.0

    def explain(
        raw_value: float, normalized_value: float, weight: float, weighted_score: float
    ) -> str:
        return (
            f"Sum of historical pair-frequency counts across this ticket's "
            f"number pairs is {raw_value:.0f} (most frequent pair seen "
            f"{max_pair_count} times)."
        )

    return Feature(
        name="pair",
        extractor=extractor,
        weight=weight,
        normalizer=normalizer,
        explain=explain,
    )


def build_hot_score_feature(
    df: pd.DataFrame, numbers_count: int = 5, weight: float = 1.0
) -> Feature:
    """Build a feature scoring tickets by individual number frequency.

    Args:
        df: Historical draw data, as returned by ``utils.loader.load_lottery``.
        numbers_count: How many main numbers each ticket has.
        weight: Weight applied to this feature's normalized value.

    Returns:
        A ``Feature`` named ``"hot"`` (rendered as the ``HotScore``
        output column).
    """
    freq = number_frequency(df)
    max_count = max(freq.values(), default=1)
    max_raw = max_count * numbers_count

    def extractor(ticket: Ticket) -> float:
        return float(sum(freq.get(n, 0) for n in ticket.numbers))

    def normalizer(raw_value: float) -> float:
        return raw_value / max_raw if max_raw else 0.0

    def explain(
        raw_value: float, normalized_value: float, weight: float, weighted_score: float
    ) -> str:
        return (
            f"Sum of individual number frequencies is {raw_value:.0f} "
            f"(hottest number seen {max_count} times)."
        )

    return Feature(
        name="hot",
        extractor=extractor,
        weight=weight,
        normalizer=normalizer,
        explain=explain,
    )


def build_odd_even_score_feature(
    numbers_count: int = 5, weight: float = 1.0
) -> Feature:
    """Build a feature rewarding a balanced odd/even number split.

    Args:
        numbers_count: How many main numbers each ticket has.
        weight: Weight applied to this feature's normalized value.

    Returns:
        A ``Feature`` named ``"odd_even"`` (rendered as the
        ``OddEvenScore`` output column).
    """

    def extractor(ticket: Ticket) -> float:
        return float(sum(1 for n in ticket.numbers if n % 2 == 1))

    def normalizer(odd_count: float) -> float:
        even_count = numbers_count - odd_count
        imbalance = abs(odd_count - even_count)
        return max(0.0, 1.0 - imbalance / numbers_count)

    def explain(
        raw_value: float, normalized_value: float, weight: float, weighted_score: float
    ) -> str:
        odd = int(raw_value)
        even = numbers_count - odd
        return f"{odd} odd / {even} even numbers (balance score {normalized_value:.2f})."

    return Feature(
        name="odd_even",
        extractor=extractor,
        weight=weight,
        normalizer=normalizer,
        explain=explain,
    )


def build_default_features(df: pd.DataFrame, numbers_count: int = 5) -> list[Feature]:
    """Build the default explainable feature set.

    Args:
        df: Historical draw data, as returned by ``utils.loader.load_lottery``.
        numbers_count: How many main numbers each ticket has.

    Returns:
        ``[PairScore feature, HotScore feature, OddEvenScore feature]``.
    """
    return [
        build_pair_score_feature(df, numbers_count=numbers_count),
        build_hot_score_feature(df, numbers_count=numbers_count),
        build_odd_even_score_feature(numbers_count=numbers_count),
    ]
