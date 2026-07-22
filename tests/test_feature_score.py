from core.feature_score import Feature, FeatureScore, ScoringEngine, TicketScore
from core.ticket import Ticket


def make_ticket(numbers=None, special=7):
    return Ticket(
        numbers=numbers or [1, 2, 3, 4, 5],
        special=special,
        score=0.0,
        method="test",
    )


def test_score_computes_weighted_contribution_per_feature():
    feature = Feature(
        name="sum_of_numbers",
        extractor=lambda t: sum(t.numbers),
        weight=2.0,
        normalizer=lambda v: v / 100,
    )
    engine = ScoringEngine()

    result = engine.score(make_ticket([1, 2, 3, 4, 5]), features=[feature])

    assert len(result.feature_scores) == 1
    fs = result.feature_scores[0]
    assert isinstance(fs, FeatureScore)
    assert fs.feature_name == "sum_of_numbers"
    assert fs.raw_value == 15
    assert fs.normalized_value == 0.15
    assert fs.weight == 2.0
    assert fs.score == 0.3


def test_score_returns_total_score_as_sum_of_feature_scores():
    features = [
        Feature(name="a", extractor=lambda t: 1.0, weight=1.0),
        Feature(name="b", extractor=lambda t: 2.0, weight=3.0),
    ]
    engine = ScoringEngine()

    result = engine.score(make_ticket(), features=features)

    assert isinstance(result, TicketScore)
    assert result.total_score == 1.0 * 1.0 + 2.0 * 3.0


def test_score_defaults_to_identity_normalizer():
    feature = Feature(name="special", extractor=lambda t: t.special, weight=1.0)
    engine = ScoringEngine()

    result = engine.score(make_ticket(special=9), features=[feature])

    fs = result.feature_scores[0]
    assert fs.raw_value == 9
    assert fs.normalized_value == 9
    assert fs.score == 9


def test_score_with_no_features_returns_zero_total():
    engine = ScoringEngine()

    result = engine.score(make_ticket())

    assert result.feature_scores == []
    assert result.total_score == 0.0


def test_score_uses_engine_configured_features_when_none_passed():
    feature = Feature(name="constant", extractor=lambda t: 5.0, weight=2.0)
    engine = ScoringEngine(features=[feature])

    result = engine.score(make_ticket())

    assert result.total_score == 10.0


def test_score_all_scores_every_ticket_in_order():
    feature = Feature(name="numbers_len", extractor=lambda t: len(t.numbers), weight=1.0)
    engine = ScoringEngine(features=[feature])

    tickets = [make_ticket([1, 2, 3]), make_ticket([1, 2, 3, 4, 5])]
    results = engine.score_all(tickets)

    assert [r.total_score for r in results] == [3.0, 5.0]
    assert [r.ticket for r in results] == tickets


def test_score_all_with_no_tickets_returns_empty_list():
    engine = ScoringEngine()

    assert engine.score_all([]) == []


def test_feature_score_exposes_explainability_aliases():
    feature = Feature(
        name="sum_of_numbers",
        extractor=lambda t: sum(t.numbers),
        weight=2.0,
        normalizer=lambda v: v / 100,
    )
    engine = ScoringEngine()

    fs = engine.score(make_ticket([1, 2, 3, 4, 5]), features=[feature]).feature_scores[0]

    assert fs.raw_score == fs.raw_value
    assert fs.weighted_score == fs.score
    assert isinstance(fs.explanation, str)
    assert fs.explanation != ""


def test_feature_score_uses_custom_explain_callable():
    feature = Feature(
        name="custom",
        extractor=lambda t: 4.0,
        weight=1.0,
        explain=lambda raw, norm, weight, weighted: f"custom explanation: {raw}",
    )
    engine = ScoringEngine()

    fs = engine.score(make_ticket(), features=[feature]).feature_scores[0]

    assert fs.explanation == "custom explanation: 4.0"
