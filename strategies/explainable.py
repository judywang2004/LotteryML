"""Explainable ticket prediction strategy combining named, weighted features."""

from __future__ import annotations

from typing import Any

import pandas as pd

from core.feature_score import ScoringEngine
from core.prediction import (
    CandidateGenerator,
    Prediction,
    PredictionPipeline,
    prediction_to_record,
)
from features.scoring_features import build_default_features
from models.registry import register
from utils.loader import load_lottery

METHOD_NAME = "explainable"

NUMBER_COLUMNS = ["N1", "N2", "N3", "N4", "N5"]
CANDIDATE_POOL_MULTIPLIER = 20
MIN_CANDIDATE_POOL = 200


def score_candidates(
    df: pd.DataFrame,
    total_predictions: int = 20,
    random_seed: int | None = None,
) -> list[Prediction]:
    """Generate random candidate tickets and rank them by explainable features.

    Pipeline: ``CandidateGenerator -> ScoringEngine (PairScore, HotScore,
    OddEvenScore) -> sort by TotalScore -> top N``.

    Args:
        df: Historical draw data, as returned by ``utils.loader.load_lottery``.
        total_predictions: Number of top-ranked predictions to return.
        random_seed: Optional seed for reproducible candidate generation.

    Returns:
        The ``total_predictions`` highest-scoring predictions, each
        carrying its per-feature score breakdown.
    """
    max_number = int(df[NUMBER_COLUMNS].values.max())
    special_max = int(df["SpecialBall"].max())

    candidate_generator = CandidateGenerator(
        number_of_candidates=max(
            total_predictions * CANDIDATE_POOL_MULTIPLIER, MIN_CANDIDATE_POOL
        ),
        random_seed=random_seed,
        max_number=max_number,
        special_max=special_max,
        method_name=METHOD_NAME,
    )
    scoring_engine = ScoringEngine(features=build_default_features(df))

    pipeline = PredictionPipeline(
        candidate_generator=candidate_generator,
        scoring_engine=scoring_engine,
        top_n=total_predictions,
        strategy_name=METHOD_NAME,
    )

    return pipeline.generate()


def generate(
    game: str,
    total_predictions: int = 20,
    random_seed: int | None = None,
    df: pd.DataFrame | None = None,
) -> list[dict[str, Any]]:
    """Registry entry point: load ``game`` data and predict explainable tickets.

    Args:
        game: Lottery game name understood by ``utils.loader.load_lottery``.
        total_predictions: Number of top-ranked predictions to return.
        random_seed: Optional seed for reproducible candidate generation.
        df: Historical draw data to use instead of loading it via
            ``utils.loader.load_lottery``. Lets callers (e.g. a
            backtesting engine) score against a limited training window.

    Returns:
        Prediction records (one dict per ticket) with a ``TotalScore``
        column plus one ``<Feature>Score`` column per configured feature
        (``PairScore``, ``HotScore``, ``OddEvenScore``), matching the
        format ``utils.writer.save_predictions`` already expects.
    """
    if df is None:
        df = load_lottery(game)
    predictions = score_candidates(df, total_predictions, random_seed)

    return [prediction_to_record(prediction) for prediction in predictions]


register(METHOD_NAME, generate)
