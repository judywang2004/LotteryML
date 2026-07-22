import pandas as pd
import pytest

from core.ticket import Ticket
from features.scoring_features import (
    build_default_features,
    build_hot_score_feature,
    build_odd_even_score_feature,
    build_pair_score_feature,
)


@pytest.fixture
def draws_df():
    return pd.DataFrame(
        {
            "N1": [1, 1, 1, 2],
            "N2": [2, 2, 2, 3],
            "N3": [10, 11, 12, 13],
            "N4": [20, 21, 22, 23],
            "N5": [30, 31, 32, 33],
            "SpecialBall": [5, 6, 7, 8],
        }
    )


def ticket(numbers):
    return Ticket(numbers=numbers, special=1, score=0.0, method="test")


def test_pair_score_feature_rewards_frequent_pairs(draws_df):
    feature = build_pair_score_feature(draws_df)

    frequent = feature.extractor(ticket([1, 2, 40, 41, 42]))
    rare = feature.extractor(ticket([40, 41, 42, 43, 44]))

    assert feature.name == "pair"
    assert frequent > rare


def test_pair_score_feature_normalizes_between_zero_and_one(draws_df):
    feature = build_pair_score_feature(draws_df)

    raw = feature.extractor(ticket([1, 2, 10, 20, 30]))
    normalized = feature.normalizer(raw)

    assert 0.0 <= normalized <= 1.0


def test_hot_score_feature_rewards_frequent_numbers(draws_df):
    feature = build_hot_score_feature(draws_df)

    hot = feature.extractor(ticket([1, 2, 40, 41, 42]))
    cold = feature.extractor(ticket([40, 41, 42, 43, 44]))

    assert feature.name == "hot"
    assert hot > cold


def test_odd_even_score_feature_rewards_balanced_split():
    feature = build_odd_even_score_feature(numbers_count=5)

    balanced = feature.normalizer(feature.extractor(ticket([1, 2, 3, 4, 6])))  # 3 odd / 2 even
    all_odd = feature.normalizer(feature.extractor(ticket([1, 3, 5, 7, 9])))

    assert feature.name == "odd_even"
    assert balanced > all_odd


def test_odd_even_score_feature_explanation_reports_counts():
    feature = build_odd_even_score_feature(numbers_count=5)

    raw = feature.extractor(ticket([1, 3, 5, 7, 9]))
    normalized = feature.normalizer(raw)
    explanation = feature.explain(raw, normalized, feature.weight, raw * feature.weight)

    assert "5 odd" in explanation
    assert "0 even" in explanation


def test_build_default_features_returns_pair_hot_odd_even(draws_df):
    features = build_default_features(draws_df)

    assert [f.name for f in features] == ["pair", "hot", "odd_even"]
