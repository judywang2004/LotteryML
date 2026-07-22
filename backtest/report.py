"""CSV/JSON report generation for backtest runs."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.engine import BacktestRun
from backtest.metrics import BacktestMetrics, compute_metrics


def _draw_result_records(run: BacktestRun) -> list[dict[str, Any]]:
    """Flatten every draw's predictions into per-prediction report rows."""
    records = []
    for draw_result in run.draw_results:
        for prediction, match_count, special_match in zip(
            draw_result.predictions,
            draw_result.match_counts,
            draw_result.special_matches,
        ):
            records.append(
                {
                    "draw_date": (
                        str(draw_result.draw_date)
                        if draw_result.draw_date is not None
                        else None
                    ),
                    "actual_numbers": draw_result.actual_numbers,
                    "actual_special": draw_result.actual_special,
                    "predicted_numbers": prediction.get("numbers"),
                    "predicted_special": prediction.get("special"),
                    "match_count": match_count,
                    "special_match": special_match,
                }
            )
    return records


def generate_report(
    run: BacktestRun,
    output_dir: str | Path = "output/backtest",
) -> dict[str, Path]:
    """Write CSV and JSON backtest reports to disk.

    The CSV contains one row per individual prediction (draw actuals,
    predicted numbers/special, and match outcome). The JSON contains the
    same rows plus the aggregate :class:`~backtest.metrics.BacktestMetrics`
    for the run.

    Args:
        run: The completed backtest run to report on.
        output_dir: Base directory for report output; files are written
            to ``<output_dir>/<game>/<method>/``.

    Returns:
        ``{"csv": path, "json": path}`` for the files that were written.
    """
    metrics: BacktestMetrics = compute_metrics(run)
    records = _draw_result_records(run)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = Path(output_dir) / run.game / run.method
    folder.mkdir(parents=True, exist_ok=True)

    csv_file = folder / f"{timestamp}.csv"
    json_file = folder / f"{timestamp}.json"

    pd.DataFrame(records).to_csv(csv_file, index=False)

    payload = {
        "game": run.game,
        "method": run.method,
        "train_size": run.train_size,
        "top_n": run.top_n,
        "metrics": asdict(metrics),
        "results": records,
    }

    with open(json_file, "w") as f:
        json.dump(payload, f, indent=4, default=str)

    return {"csv": csv_file, "json": json_file}
