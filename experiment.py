"""CLI: backtest and compare multiple prediction methods over a date split.

Filters historical draws to ``--train-start .. end``, trains each method
on everything before ``--test-start``, then walks forward through the
remaining draws (via ``backtest.engine.BacktestEngine``) predicting
``--top-n`` tickets per draw. Prints a comparison table and writes a
full CSV/JSON report per method.
"""

from __future__ import annotations

import argparse

import pandas as pd

import models.frequency  # noqa: F401  (registers "frequency")
import models.hot_numbers  # noqa: F401  (registers "hot")
import strategies.explainable  # noqa: F401  (registers "explainable")
import strategies.pair  # noqa: F401  (registers "pair")
from backtest.engine import BacktestEngine, BacktestRun
from backtest.metrics import compute_metrics
from backtest.ranking import compute_ranking_metrics
from backtest.report import generate_report
from utils.loader import load_lottery


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the experiment CLI."""
    parser = argparse.ArgumentParser(
        description="Backtest and compare prediction methods over a date-based train/test split."
    )
    parser.add_argument("--game", required=True)
    parser.add_argument("--methods", nargs="+", required=True)
    parser.add_argument("--train-start", required=True)
    parser.add_argument("--test-start", required=True)
    parser.add_argument("--top-n", type=int, default=20)
    return parser.parse_args()


def build_train_window(
    df: pd.DataFrame, train_start: str, test_start: str
) -> tuple[pd.DataFrame, int]:
    """Slice historical draws to the requested date range and locate the split.

    Args:
        df: Historical draw data, as returned by ``utils.loader.load_lottery``.
        train_start: Earliest draw date (inclusive) to include, e.g. ``"2015-01-01"``.
        test_start: First draw date (inclusive) to backtest against.

    Returns:
        A tuple of ``(windowed_df, train_size)`` where ``windowed_df`` is
        sorted chronologically starting at ``train_start`` and
        ``train_size`` is the number of draws strictly before ``test_start``.

    Raises:
        SystemExit: If the split leaves nothing to train on or nothing to test on.
    """
    sorted_df = df.sort_values("DrawDate").reset_index(drop=True)
    windowed = sorted_df[sorted_df["DrawDate"] >= pd.Timestamp(train_start)].reset_index(
        drop=True
    )
    train_size = int((windowed["DrawDate"] < pd.Timestamp(test_start)).sum())

    if train_size == 0:
        raise SystemExit(f"No draws found between {train_start} and {test_start}")
    if train_size >= len(windowed):
        raise SystemExit(f"No draws found on/after {test_start} to backtest against")

    return windowed, train_size


def print_comparison_row(method: str, run: BacktestRun) -> None:
    """Print one comparison-table row for a method's backtest results."""
    metrics = compute_metrics(run)
    ranking = compute_ranking_metrics(run)

    avg_rank = "-" if ranking.average_rank is None else f"{ranking.average_rank:.2f}"

    print(
        f"{method:<12} {len(run.draw_results):>6} {metrics.match5:>7} {metrics.match4:>7} "
        f"{metrics.match3:>7} {metrics.mega_ball:>9} {metrics.average_score:>9.3f} "
        f"{ranking.top1_hit:>7.2%} {ranking.top10_hit:>7.2%} {avg_rank:>8} "
        f"{ranking.prediction_coverage:>9.2%}"
    )


def main() -> None:
    """Run the backtest comparison for every requested method and print results."""
    args = parse_args()

    df = load_lottery(args.game)
    windowed, train_size = build_train_window(df, args.train_start, args.test_start)

    engine = BacktestEngine()

    header = (
        f"{'Method':<12} {'Draws':>6} {'Match5':>7} {'Match4':>7} {'Match3':>7} "
        f"{'MegaBall':>9} {'AvgScore':>9} {'Top1':>7} {'Top10':>7} {'AvgRank':>8} {'Coverage':>9}"
    )
    print(header)
    print("-" * len(header))

    for method in args.methods:
        run = engine.run(
            game=args.game,
            method=method,
            train_size=train_size,
            top_n=args.top_n,
            df=windowed,
        )
        print_comparison_row(method, run)

        report_paths = generate_report(run)
        print(f"  report: {report_paths['csv']}")


if __name__ == "__main__":
    main()
