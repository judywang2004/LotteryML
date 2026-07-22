import pandas as pd
import pytest

import models.hot_numbers  # noqa: F401  (registers "hot")
from backtest.engine import BacktestEngine, BacktestRun, DrawResult
from backtest.ranking import RankingMetrics, compute_ranking_metrics


def draw(match_counts, num_predictions=None):
    n = num_predictions if num_predictions is not None else len(match_counts)
    return DrawResult(
        draw_date=None,
        actual_numbers=[1, 2, 3, 4, 5],
        actual_special=1,
        predictions=[{"numbers": [], "special": 0} for _ in range(n)],
        match_counts=match_counts,
        special_matches=[False] * n,
    )


def make_run(draw_results, top_n=5):
    return BacktestRun(game="g", method="m", train_size=1, top_n=top_n, draw_results=draw_results)


def test_hit_at_rank_1_counts_toward_every_top_k():
    run = make_run([draw([5, 0, 0, 0, 0])])

    metrics = compute_ranking_metrics(run)

    assert isinstance(metrics, RankingMetrics)
    assert metrics.top1_hit == 1.0
    assert metrics.top5_hit == 1.0
    assert metrics.top10_hit == 1.0
    assert metrics.best_rank == 1
    assert metrics.average_rank == 1.0
    assert metrics.median_rank == 1.0


def test_hit_only_at_rank_5_excluded_from_top1_but_included_in_top5():
    run = make_run([draw([0, 0, 0, 0, 5])])

    metrics = compute_ranking_metrics(run)

    assert metrics.top1_hit == 0.0
    assert metrics.top5_hit == 1.0
    assert metrics.top10_hit == 1.0
    assert metrics.best_rank == 5


def test_no_hit_gives_zero_hit_rates_and_none_rank_stats():
    run = make_run([draw([0, 1, 2, 0, 1])])

    metrics = compute_ranking_metrics(run)

    assert metrics.top1_hit == 0.0
    assert metrics.top100_hit == 0.0
    assert metrics.average_rank is None
    assert metrics.median_rank is None
    assert metrics.best_rank is None


def test_only_first_hit_per_draw_counts_toward_rank():
    run = make_run([draw([0, 3, 4, 0, 0])])  # hits at rank 2 and 3

    metrics = compute_ranking_metrics(run)

    assert metrics.best_rank == 2
    assert metrics.average_rank == 2.0


def test_average_and_median_rank_across_multiple_draws():
    run = make_run(
        [
            draw([5, 0, 0, 0, 0]),  # rank 1
            draw([0, 0, 0, 3, 0]),  # rank 4
            draw([0, 0, 0, 0, 0]),  # no hit
        ]
    )

    metrics = compute_ranking_metrics(run)

    assert metrics.average_rank == (1 + 4) / 2
    assert metrics.median_rank == (1 + 4) / 2
    assert metrics.best_rank == 1
    assert metrics.top1_hit == 1 / 3
    assert metrics.top5_hit == 2 / 3


def test_custom_hit_threshold_changes_what_counts_as_a_hit():
    run = make_run([draw([2, 2, 2, 2, 2])])

    strict = compute_ranking_metrics(run, hit_threshold=3)
    lenient = compute_ranking_metrics(run, hit_threshold=2)

    assert strict.top1_hit == 0.0
    assert strict.best_rank is None
    assert lenient.top1_hit == 1.0
    assert lenient.best_rank == 1


def test_prediction_coverage_reflects_partial_delivery():
    run = make_run(
        [
            draw([0, 0], num_predictions=2),  # 2 of 5 requested
            draw([0, 0, 0, 0, 0], num_predictions=5),  # full 5 of 5
        ],
        top_n=5,
    )

    metrics = compute_ranking_metrics(run)

    assert metrics.prediction_coverage == pytest.approx((2 / 5 + 5 / 5) / 2)


def test_empty_run_returns_zero_rates_and_none_ranks():
    run = make_run([])

    metrics = compute_ranking_metrics(run)

    assert metrics.total_draws == 0
    assert metrics.top1_hit == 0.0
    assert metrics.top100_hit == 0.0
    assert metrics.average_rank is None
    assert metrics.median_rank is None
    assert metrics.best_rank is None
    assert metrics.prediction_coverage == 0.0


def test_hit_threshold_is_recorded_on_the_result():
    run = make_run([draw([5])])

    metrics = compute_ranking_metrics(run, hit_threshold=4)

    assert metrics.hit_threshold == 4


def test_integration_with_real_backtest_engine_output():
    rows = [
        {
            "N1": i + 1,
            "N2": i + 2,
            "N3": i + 3,
            "N4": i + 4,
            "N5": i + 5,
            "SpecialBall": i + 1,
        }
        for i in range(8)
    ]
    history_df = pd.DataFrame(rows)
    history_df["DrawDate"] = pd.date_range("2020-01-01", periods=8, freq="D")

    engine = BacktestEngine()
    run = engine.run(game="testgame", method="hot", train_size=5, top_n=3, df=history_df)

    metrics = compute_ranking_metrics(run)

    assert metrics.total_draws == len(run.draw_results)
    assert 0.0 <= metrics.top1_hit <= 1.0
    assert 0.0 <= metrics.prediction_coverage <= 1.0
