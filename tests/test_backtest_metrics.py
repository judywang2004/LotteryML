from backtest.engine import BacktestRun, DrawResult
from backtest.metrics import BacktestMetrics, compute_metrics


def make_run(draw_results):
    return BacktestRun(game="g", method="m", train_size=1, top_n=1, draw_results=draw_results)


def test_compute_metrics_tallies_match_counts_and_mega_ball():
    draw_results = [
        DrawResult(
            draw_date=None,
            actual_numbers=[1, 2, 3, 4, 5],
            actual_special=10,
            predictions=[
                {"numbers": [1, 2, 3, 4, 5], "special": 10, "score": 1.0},
                {"numbers": [1, 2, 3, 6, 7], "special": 11, "score": 0.5},
            ],
            match_counts=[5, 3],
            special_matches=[True, False],
        ),
        DrawResult(
            draw_date=None,
            actual_numbers=[8, 9, 10, 11, 12],
            actual_special=1,
            predictions=[
                {"numbers": [8, 9, 100, 101, 102], "special": 1, "score": 2.0},
            ],
            match_counts=[2],
            special_matches=[True],
        ),
    ]

    metrics = compute_metrics(make_run(draw_results))

    assert isinstance(metrics, BacktestMetrics)
    assert metrics.match5 == 1
    assert metrics.match4 == 0
    assert metrics.match3 == 1
    assert metrics.match2 == 1
    assert metrics.match1 == 0
    assert metrics.mega_ball == 2
    assert metrics.total_predictions == 3
    assert metrics.average_score == (1.0 + 0.5 + 2.0) / 3


def test_compute_metrics_prefers_total_score_key_over_score():
    draw_results = [
        DrawResult(
            draw_date=None,
            actual_numbers=[1, 2, 3, 4, 5],
            actual_special=1,
            predictions=[
                {"numbers": [1, 2, 3, 4, 5], "special": 1, "score": 0.1, "TotalScore": 9.0}
            ],
            match_counts=[5],
            special_matches=[True],
        ),
    ]

    metrics = compute_metrics(make_run(draw_results))

    assert metrics.average_score == 9.0


def test_compute_metrics_defaults_score_to_zero_when_absent():
    draw_results = [
        DrawResult(
            draw_date=None,
            actual_numbers=[1, 2, 3, 4, 5],
            actual_special=1,
            predictions=[{"numbers": [1, 2, 3, 4, 5], "special": 1, "method": "Frequency"}],
            match_counts=[5],
            special_matches=[True],
        ),
    ]

    metrics = compute_metrics(make_run(draw_results))

    assert metrics.average_score == 0.0


def test_compute_metrics_with_no_draw_results():
    metrics = compute_metrics(make_run([]))

    assert metrics.total_predictions == 0
    assert metrics.average_score == 0.0
    assert metrics.match5 == 0
