"""Aggregate scoring metrics for a completed backtest run."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backtest.engine import BacktestRun


@dataclass
class BacktestMetrics:
    """Aggregate match-tier counts and average score across a backtest run.

    Counts are over individual predictions (every top-N candidate for
    every backtested draw), not over draws.

    Attributes:
        match5: Predictions that matched all 5 main numbers.
        match4: Predictions that matched exactly 4 main numbers.
        match3: Predictions that matched exactly 3 main numbers.
        match2: Predictions that matched exactly 2 main numbers.
        match1: Predictions that matched exactly 1 main number.
        mega_ball: Predictions whose special number matched.
        average_score: Mean of each prediction's reported score, or
            ``0.0`` if no predictions carried a score.
        total_predictions: Total number of individual predictions evaluated.
    """

    match5: int
    match4: int
    match3: int
    match2: int
    match1: int
    mega_ball: int
    average_score: float
    total_predictions: int


def _extract_score(prediction: dict[str, Any]) -> float:
    """Extract a numeric score from a prediction record.

    Prefers ``TotalScore`` (used by the explainable strategy), then
    ``score`` (used by the pair strategy), falling back to ``0.0`` for
    strategies that report no score (frequency, hot).
    """
    if "TotalScore" in prediction:
        return float(prediction["TotalScore"])
    if "score" in prediction:
        return float(prediction["score"])
    return 0.0


def compute_metrics(run: BacktestRun) -> BacktestMetrics:
    """Compute aggregate metrics across every prediction in a backtest run.

    Args:
        run: The completed backtest run to summarize.

    Returns:
        Match-tier counts, mega-ball match count, and average score
        across every individual prediction made during the run.
    """
    match_tally = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    mega_ball = 0
    scores: list[float] = []

    for draw_result in run.draw_results:
        for match_count, special_match, prediction in zip(
            draw_result.match_counts,
            draw_result.special_matches,
            draw_result.predictions,
        ):
            if match_count in match_tally:
                match_tally[match_count] += 1
            if special_match:
                mega_ball += 1
            scores.append(_extract_score(prediction))

    average_score = sum(scores) / len(scores) if scores else 0.0

    return BacktestMetrics(
        match5=match_tally[5],
        match4=match_tally[4],
        match3=match_tally[3],
        match2=match_tally[2],
        match1=match_tally[1],
        mega_ball=mega_ball,
        average_score=average_score,
        total_predictions=len(scores),
    )
