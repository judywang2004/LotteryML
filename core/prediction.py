"""Prediction pipeline: candidate generation, scoring, and ranking."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from core.feature_score import FeatureScore, ScoringEngine
from core.ticket import Ticket


@dataclass
class Prediction:
    """A final, ranked prediction produced by a :class:`PredictionGenerator`.

    Attributes:
        numbers: The main numbers picked for the prediction.
        special_ball: The special number (e.g. Powerball/Mega Ball).
        feature_scores: Per-feature scoring breakdown that produced
            ``total_score``.
        total_score: Overall score used to rank this prediction.
        strategy: Name of the strategy/pipeline that produced the prediction.
        metadata: Free-form extra information about how the prediction
            was generated (e.g. the candidate's original method, seed).
    """

    numbers: list[int]
    special_ball: int
    feature_scores: list[FeatureScore]
    total_score: float
    strategy: str
    metadata: dict[str, Any] = field(default_factory=dict)


def _feature_column_name(feature_name: str) -> str:
    """Convert a ``snake_case`` feature name into a ``PascalCaseScore`` column name."""
    return "".join(part.capitalize() for part in feature_name.split("_")) + "Score"


def prediction_to_record(prediction: Prediction) -> dict[str, Any]:
    """Flatten a prediction into a CSV/JSON-friendly record.

    Produces one column per feature score (e.g. ``PairScore``,
    ``HotScore``, ``OddEvenScore``) alongside ``TotalScore``, so each
    feature's contribution is visible in exported predictions.

    Args:
        prediction: The prediction to flatten.

    Returns:
        A flat dict suitable for ``pandas.DataFrame`` construction or
        ``json.dump``, as used by ``utils.writer.save_predictions``.
    """
    record: dict[str, Any] = dict(prediction.metadata)
    record.update(
        {
            "numbers": prediction.numbers,
            "special": prediction.special_ball,
            "method": prediction.strategy,
            "TotalScore": prediction.total_score,
        }
    )

    for feature_score in prediction.feature_scores:
        record[_feature_column_name(feature_score.feature_name)] = (
            feature_score.weighted_score
        )

    return record


class PredictionGenerator(ABC):
    """Interface for anything that produces ranked predictions."""

    @abstractmethod
    def generate(self) -> list[Prediction]:
        """Generate predictions.

        Returns:
            Predictions produced by this generator.
        """
        raise NotImplementedError


class CandidateGenerator:
    """Generates random, valid lottery ticket candidates."""

    def __init__(
        self,
        number_of_candidates: int,
        random_seed: int | None = None,
        numbers_count: int = 5,
        max_number: int = 69,
        special_max: int = 26,
        method_name: str = "random_candidate",
    ) -> None:
        """Configure the candidate generator.

        Args:
            number_of_candidates: How many candidate tickets to generate.
            random_seed: Seed for the internal random number generator.
                Using the same seed reproduces the same candidates.
                Defaults to ``None``, which uses nondeterministic randomness.
            numbers_count: How many distinct main numbers each ticket has.
            max_number: Highest valid main number (inclusive); main
                numbers are drawn from ``1..max_number``.
            special_max: Highest valid special number (inclusive); the
                special number is drawn from ``1..special_max``.
            method_name: Value stored in each generated ticket's
                ``method`` field.
        """
        self.number_of_candidates = number_of_candidates
        self.random_seed = random_seed
        self.numbers_count = numbers_count
        self.max_number = max_number
        self.special_max = special_max
        self.method_name = method_name

    def generate_candidates(self) -> list[Ticket]:
        """Generate the configured number of random valid tickets.

        Returns:
            Randomly generated tickets, each with distinct, sorted main
            numbers and a single special number, all within valid ranges.
        """
        rng = random.Random(self.random_seed)

        candidates = []
        for _ in range(self.number_of_candidates):
            numbers = sorted(
                rng.sample(range(1, self.max_number + 1), self.numbers_count)
            )
            special = rng.randint(1, self.special_max)

            candidates.append(
                Ticket(
                    numbers=numbers,
                    special=special,
                    score=0.0,
                    method=self.method_name,
                )
            )

        return candidates


class PredictionPipeline(PredictionGenerator):
    """Generates predictions by scoring and ranking random candidates.

    Pipeline: ``CandidateGenerator -> ScoringEngine -> sort by total_score
    -> top N``.
    """

    def __init__(
        self,
        candidate_generator: CandidateGenerator,
        scoring_engine: ScoringEngine,
        top_n: int,
        strategy_name: str = "prediction_pipeline",
    ) -> None:
        """Configure the pipeline.

        Args:
            candidate_generator: Produces the candidate tickets to score.
            scoring_engine: Scores each candidate ticket.
            top_n: Number of highest-scoring predictions to return.
            strategy_name: Value stored in each prediction's ``strategy``
                field.
        """
        self.candidate_generator = candidate_generator
        self.scoring_engine = scoring_engine
        self.top_n = top_n
        self.strategy_name = strategy_name

    def generate(self) -> list[Prediction]:
        """Run the full candidate-generation-to-prediction pipeline.

        Returns:
            The ``top_n`` predictions, sorted by descending total score.
        """
        candidates = self.candidate_generator.generate_candidates()
        ticket_scores = self.scoring_engine.score_all(candidates)

        ranked = sorted(
            ticket_scores, key=lambda ts: ts.total_score, reverse=True
        )

        return [
            Prediction(
                numbers=ticket_score.ticket.numbers,
                special_ball=ticket_score.ticket.special,
                feature_scores=ticket_score.feature_scores,
                total_score=ticket_score.total_score,
                strategy=self.strategy_name,
                metadata={"method": ticket_score.ticket.method},
            )
            for ticket_score in ranked[: self.top_n]
        ]
