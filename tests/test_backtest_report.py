import json

import pandas as pd

from backtest.engine import BacktestRun, DrawResult
from backtest.report import generate_report


def make_run():
    draw_results = [
        DrawResult(
            draw_date=None,
            actual_numbers=[1, 2, 3, 4, 5],
            actual_special=10,
            predictions=[{"numbers": [1, 2, 3, 4, 5], "special": 10, "score": 1.0}],
            match_counts=[5],
            special_matches=[True],
        ),
    ]
    return BacktestRun(
        game="testgame", method="frequency", train_size=1, top_n=1, draw_results=draw_results
    )


def test_generate_report_writes_csv_and_json(tmp_path):
    run = make_run()

    paths = generate_report(run, output_dir=tmp_path)

    assert paths["csv"].exists()
    assert paths["json"].exists()
    assert paths["csv"].parent == tmp_path / "testgame" / "frequency"


def test_generate_report_json_includes_metrics_and_results(tmp_path):
    run = make_run()

    paths = generate_report(run, output_dir=tmp_path)

    with open(paths["json"]) as f:
        payload = json.load(f)

    assert payload["game"] == "testgame"
    assert payload["method"] == "frequency"
    assert payload["metrics"]["match5"] == 1
    assert payload["metrics"]["total_predictions"] == 1
    assert len(payload["results"]) == 1
    assert payload["results"][0]["match_count"] == 5


def test_generate_report_csv_has_one_row_per_prediction(tmp_path):
    run = make_run()

    paths = generate_report(run, output_dir=tmp_path)

    df = pd.read_csv(paths["csv"])
    assert len(df) == 1
    assert "match_count" in df.columns
