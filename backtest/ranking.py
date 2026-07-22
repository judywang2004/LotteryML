"""Ranking-quality evaluation for backtested predictions.

Complements ``backtest.metrics`` (which tallies raw match tiers) by
evaluating how well the ORDER of a method's ranked predictions locates
a "winning" ticket for each backtested draw. A prediction's rank is its
1-indexed position within a draw's prediction list (rank 1 = the
method's top-ranked pick).
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from backtest.engine import BacktestRun, DrawResult

TOP_K_VALUES = (1, 5, 10, 20, 50, 100)
DEFAULT_HIT_THRESHOLD = 3


@dataclass
class RankingMetrics:
    """Ranking-quality metrics for a backtest run.

    A prediction "hits" when its main-number match count is at least
    ``hit_threshold``. A draw's rank is the 1-indexed position of the
    first hit among that draw's ranked predictions, or ``None`` if none
    of the returned predictions hit.

    Attributes:
        top1_hit: Fraction of draws with a hit within the top 1 prediction.
        top5_hit: Fraction of draws with a hit within the top 5 predictions.
        top10_hit: Fraction of draws with a hit within the top 10 predictions.
        top20_hit: Fraction of draws with a hit within the top 20 predictions.
        top50_hit: Fraction of draws with a hit within the top 50 predictions.
        top100_hit: Fraction of draws with a hit within the top 100 predictions.
        average_rank: Mean rank across draws that had a hit, or ``None``
            if no draw had a hit.
        median_rank: Median rank across draws that had a hit, or
            ``None`` if no draw had a hit.
        best_rank: Smallest (best) rank achieved across the run, or
            ``None`` if no draw had a hit.
        prediction_coverage: Mean fraction of the requested ``top_n``
            predictions actually returned per draw (``1.0`` means every
            draw returned a full set of predictions).
        hit_threshold: Minimum main-number match count counted as a hit.
        total_draws: Number of draws evaluated.
    """

    top1_hit: float
    top5_hit: float
    top10_hit: float
    top20_hit: float
    top50_hit: float
    top100_hit: float
    average_rank: float | None
    median_rank: float | None
    best_rank: int | None
    prediction_coverage: float
    hit_threshold: int
    total_draws: int


def _first_hit_rank(draw_result: DrawResult, hit_threshold: int) -> int | None:
    """Return the 1-indexed rank of the first hit in a draw's predictions."""
    for rank, match_count in enumerate(draw_result.match_counts, start=1):
        if match_count >= hit_threshold:
            return rank
    return None


def compute_ranking_metrics(
    run: BacktestRun,
    hit_threshold: int = DEFAULT_HIT_THRESHOLD,
) -> RankingMetrics:
    """Compute ranking-quality metrics for a backtest run.

    Args:
        run: The completed backtest run to evaluate.
        hit_threshold: Minimum main-number match count for a prediction
            to count as a hit.

    Returns:
        Ranking metrics for the run. Hit rates and coverage default to
        ``0.0`` and rank statistics to ``None`` when the run has no draws
        or no draw ever produced a hit.
    """
    ranks: list[int] = []
    coverages: list[float] = []
    hit_counts = {k: 0 for k in TOP_K_VALUES}

    for draw_result in run.draw_results:
        rank = _first_hit_rank(draw_result, hit_threshold)
        if rank is not None:
            ranks.append(rank)
            for k in TOP_K_VALUES:
                if rank <= k:
                    hit_counts[k] += 1

        if run.top_n:
            coverages.append(len(draw_result.predictions) / run.top_n)

    total_draws = len(run.draw_results)

    def hit_rate(k: int) -> float:
        return hit_counts[k] / total_draws if total_draws else 0.0

    return RankingMetrics(
        top1_hit=hit_rate(1),
        top5_hit=hit_rate(5),
        top10_hit=hit_rate(10),
        top20_hit=hit_rate(20),
        top50_hit=hit_rate(50),
        top100_hit=hit_rate(100),
        average_rank=(sum(ranks) / len(ranks)) if ranks else None,
        median_rank=float(median(ranks)) if ranks else None,
        best_rank=min(ranks) if ranks else None,
        prediction_coverage=(sum(coverages) / len(coverages)) if coverages else 0.0,
        hit_threshold=hit_threshold,
        total_draws=total_draws,
    )
