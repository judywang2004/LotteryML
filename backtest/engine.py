"""Walk-forward backtesting engine for registered prediction methods."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from models.registry import get_model
from utils.loader import load_lottery

NUMBER_COLUMNS = ["N1", "N2", "N3", "N4", "N5"]


@dataclass
class DrawResult:
    """The outcome of predicting a single historical draw during a backtest.

    Attributes:
        draw_date: The draw date being predicted, if available in the data.
        actual_numbers: The main numbers that were actually drawn.
        actual_special: The special number that was actually drawn.
        predictions: Raw prediction records produced for this draw (one
            per top-N candidate), in the format returned by the
            registered prediction method.
        match_counts: Number of main numbers each prediction matched,
            aligned by index with ``predictions``.
        special_matches: Whether each prediction's special number
            matched, aligned by index with ``predictions``.
    """

    draw_date: Any
    actual_numbers: list[int]
    actual_special: int
    predictions: list[dict[str, Any]]
    match_counts: list[int]
    special_matches: list[bool]


@dataclass
class BacktestRun:
    """The full result of a walk-forward backtest.

    Attributes:
        game: Lottery game that was backtested.
        method: Registered prediction method name that was backtested.
        train_size: Number of earliest draws used to seed the first
            training window.
        top_n: Number of predictions requested per draw.
        draw_results: One :class:`DrawResult` per draw that was predicted.
    """

    game: str
    method: str
    train_size: int
    top_n: int
    draw_results: list[DrawResult]


class BacktestEngine:
    """Walk-forward backtests a registered prediction method against history.

    Workflow, repeated for every draw after the initial training window:
    train on every draw before it, predict the next draw, compare the
    prediction against what was actually drawn, and record the result.
    """

    def run(
        self,
        game: str,
        method: str,
        train_size: int,
        top_n: int,
        df: pd.DataFrame | None = None,
    ) -> BacktestRun:
        """Run a walk-forward backtest.

        Args:
            game: Lottery game to backtest, understood by
                ``utils.loader.load_lottery``.
            method: Registered prediction method name (e.g.
                ``"frequency"``, ``"hot"``, ``"pair"``, ``"explainable"``).
            train_size: Number of earliest draws used to seed the first
                training window. Must be positive.
            top_n: Number of predictions requested per draw.
            df: Historical draw data to use instead of loading it via
                ``utils.loader.load_lottery``. Primarily for testing.

        Returns:
            The full walk-forward backtest result. Empty (no draw
            results) if ``train_size`` covers the entire dataset.

        Raises:
            ValueError: If ``train_size`` is not a positive integer.
        """
        if train_size < 1:
            raise ValueError("train_size must be a positive integer")

        history = df if df is not None else load_lottery(game)
        if "DrawDate" in history.columns:
            history = history.sort_values("DrawDate").reset_index(drop=True)
        else:
            history = history.reset_index(drop=True)

        predict_fn = get_model(method)

        draw_results = []
        for i in range(train_size, len(history)):
            train_df = history.iloc[:i].reset_index(drop=True)
            actual_row = history.iloc[i]

            predictions = predict_fn(game, total_predictions=top_n, df=train_df)

            actual_numbers = sorted(int(actual_row[col]) for col in NUMBER_COLUMNS)
            actual_special = int(actual_row["SpecialBall"])

            match_counts = [
                len(set(prediction["numbers"]) & set(actual_numbers))
                for prediction in predictions
            ]
            special_matches = [
                int(prediction["special"]) == actual_special
                for prediction in predictions
            ]

            draw_results.append(
                DrawResult(
                    draw_date=actual_row.get("DrawDate"),
                    actual_numbers=actual_numbers,
                    actual_special=actual_special,
                    predictions=predictions,
                    match_counts=match_counts,
                    special_matches=special_matches,
                )
            )

        return BacktestRun(
            game=game,
            method=method,
            train_size=train_size,
            top_n=top_n,
            draw_results=draw_results,
        )
