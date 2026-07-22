"""Feature-based scoring engine for lottery ticket predictions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from core.ticket import Ticket


def _default_explanation(
    feature_name: str,
    raw_value: float,
    normalized_value: float,
    weight: float,
    weighted_score: float,
) -> str:
    """Build a generic, human-readable explanation for a feature score."""
    return (
        f"{feature_name}: raw={raw_value:.4g}, "
        f"normalized={normalized_value:.4g}, weight={weight:.4g} "
        f"-> weighted={weighted_score:.4g}"
    )


@dataclass
class FeatureScore:
    """The contribution of a single feature to a ticket's total score.

    ``raw_score`` and ``weighted_score`` are explainability-oriented
    aliases of ``raw_value`` and ``score`` respectively, kept alongside
    the original fields for backward compatibility.

    Attributes:
        feature_name: Name of the feature this score was computed for.
        score: Weighted contribution of the feature (``normalized_value * weight``).
        weight: Weight applied to the feature's normalized value.
        raw_value: Unmodified value produced by the feature's extractor.
        normalized_value: ``raw_value`` mapped onto a comparable scale
            by the feature's normalizer.
        raw_score: Alias of ``raw_value``.
        weighted_score: Alias of ``score``.
        explanation: Human-readable description of how this score was
            derived, suitable for display alongside a prediction.
    """

    feature_name: str
    score: float
    weight: float
    raw_value: float
    normalized_value: float
    raw_score: float
    weighted_score: float
    explanation: str


@dataclass
class Feature:
    """A scoring rule that derives a value from a ticket.

    Attributes:
        name: Unique identifier for the feature.
        extractor: Callable that computes a raw value from a ticket.
        weight: Multiplier applied to the normalized value.
        normalizer: Callable that maps a raw value onto a comparable
            scale (typically 0.0-1.0). Defaults to the identity function.
        explain: Optional callable that builds a human-readable
            explanation from ``(raw_value, normalized_value, weight,
            weighted_score)``. Defaults to a generic, auto-generated
            explanation when omitted.
    """

    name: str
    extractor: Callable[[Ticket], float]
    weight: float = 1.0
    normalizer: Callable[[float], float] = lambda value: value
    explain: Callable[[float, float, float, float], str] | None = None


@dataclass
class TicketScore:
    """The full scoring breakdown for a single ticket.

    Attributes:
        ticket: The ticket that was scored.
        feature_scores: Per-feature scoring breakdown.
        total_score: Sum of every feature score's weighted contribution.
    """

    ticket: Ticket
    feature_scores: list[FeatureScore]
    total_score: float


class ScoringEngine:
    """Scores tickets by combining a configurable set of features."""

    def __init__(self, features: Sequence[Feature] | None = None) -> None:
        """Initialize the engine with a default set of features.

        Args:
            features: Features used by :meth:`score_all` and, when no
                explicit ``features`` argument is given, by :meth:`score`.
        """
        self.features: list[Feature] = list(features) if features else []

    def score(
        self,
        ticket: Ticket,
        features: Sequence[Feature] | None = None,
    ) -> TicketScore:
        """Score a single ticket against a set of features.

        Args:
            ticket: The ticket to score.
            features: Features to score with. Defaults to the engine's
                configured features when omitted.

        Returns:
            The ticket's scoring breakdown, including the total score.
        """
        active_features = features if features is not None else self.features

        feature_scores = []
        for feature in active_features:
            raw_value = feature.extractor(ticket)
            normalized_value = feature.normalizer(raw_value)
            score = normalized_value * feature.weight

            if feature.explain is not None:
                explanation = feature.explain(
                    raw_value, normalized_value, feature.weight, score
                )
            else:
                explanation = _default_explanation(
                    feature.name, raw_value, normalized_value, feature.weight, score
                )

            feature_scores.append(
                FeatureScore(
                    feature_name=feature.name,
                    score=score,
                    weight=feature.weight,
                    raw_value=raw_value,
                    normalized_value=normalized_value,
                    raw_score=raw_value,
                    weighted_score=score,
                    explanation=explanation,
                )
            )

        total_score = sum(fs.score for fs in feature_scores)

        return TicketScore(
            ticket=ticket,
            feature_scores=feature_scores,
            total_score=total_score,
        )

    def score_all(self, tickets: Sequence[Ticket]) -> list[TicketScore]:
        """Score multiple tickets using the engine's configured features.

        Args:
            tickets: Tickets to score.

        Returns:
            One :class:`TicketScore` per input ticket, in the same order.
        """
        return [self.score(ticket) for ticket in tickets]
