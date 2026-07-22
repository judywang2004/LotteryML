import pandas as pd
import pytest

import models.frequency  # noqa: F401  (registers "frequency")
import models.hot_numbers  # noqa: F401  (registers "hot")
import strategies.pair  # noqa: F401  (registers "pair")
import strategies.explainable  # noqa: F401  (registers "explainable")
import models.registry as registry
from backtest.engine import BacktestEngine, BacktestRun, DrawResult


@pytest.fixture
def history_df():
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
    df = pd.DataFrame(rows)
    df["DrawDate"] = pd.date_range("2020-01-01", periods=8, freq="D")
    return df


def test_run_produces_one_draw_result_per_test_draw(history_df):
    engine = BacktestEngine()

    run = engine.run(
        game="testgame", method="frequency", train_size=5, top_n=3, df=history_df
    )

    assert isinstance(run, BacktestRun)
    assert len(run.draw_results) == 3
    assert all(isinstance(r, DrawResult) for r in run.draw_results)


def test_run_records_correct_actuals_and_match_counts(history_df):
    engine = BacktestEngine()

    run = engine.run(
        game="testgame", method="hot", train_size=5, top_n=2, df=history_df
    )

    first = run.draw_results[0]
    assert first.actual_numbers == [6, 7, 8, 9, 10]
    assert first.actual_special == 6
    assert len(first.predictions) == 2
    assert len(first.match_counts) == 2
    assert len(first.special_matches) == 2
    assert all(0 <= mc <= 5 for mc in first.match_counts)


def test_run_trains_only_on_draws_before_the_predicted_one(monkeypatch, history_df):
    seen_train_sizes = []
    original = registry.get_model("frequency")

    def spy(game, total_predictions=20, df=None):
        seen_train_sizes.append(len(df))
        return original(game, total_predictions=total_predictions, df=df)

    monkeypatch.setitem(registry.MODELS, "frequency", spy)

    engine = BacktestEngine()
    engine.run(game="testgame", method="frequency", train_size=5, top_n=1, df=history_df)

    assert seen_train_sizes == [5, 6, 7]


def test_run_raises_for_non_positive_train_size(history_df):
    engine = BacktestEngine()

    with pytest.raises(ValueError):
        engine.run(game="testgame", method="frequency", train_size=0, top_n=1, df=history_df)


def test_run_returns_empty_results_when_train_size_covers_all_data(history_df):
    engine = BacktestEngine()

    run = engine.run(game="testgame", method="frequency", train_size=8, top_n=1, df=history_df)

    assert run.draw_results == []


def test_run_works_with_pair_and_explainable_methods(history_df):
    engine = BacktestEngine()

    pair_run = engine.run(game="testgame", method="pair", train_size=6, top_n=2, df=history_df)
    explainable_run = engine.run(
        game="testgame", method="explainable", train_size=6, top_n=2, df=history_df
    )

    assert len(pair_run.draw_results) == 2
    assert len(explainable_run.draw_results) == 2
    assert all(len(r.predictions) <= 2 for r in pair_run.draw_results)
    assert all(len(r.predictions) == 2 for r in explainable_run.draw_results)
