import pandas as pd
import pytest

from core.prediction import Prediction
from models.registry import get_model
from strategies.explainable import METHOD_NAME, score_candidates


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


def test_score_candidates_returns_top_n_predictions(draws_df):
    predictions = score_candidates(draws_df, total_predictions=5, random_seed=1)

    assert len(predictions) == 5
    assert all(isinstance(p, Prediction) for p in predictions)


def test_score_candidates_predictions_carry_named_feature_scores(draws_df):
    predictions = score_candidates(draws_df, total_predictions=1, random_seed=1)

    feature_names = {fs.feature_name for fs in predictions[0].feature_scores}
    assert feature_names == {"pair", "hot", "odd_even"}


def test_score_candidates_is_reproducible_with_same_seed(draws_df):
    a = score_candidates(draws_df, total_predictions=5, random_seed=42)
    b = score_candidates(draws_df, total_predictions=5, random_seed=42)

    assert [p.numbers for p in a] == [p.numbers for p in b]
    assert [p.total_score for p in a] == [p.total_score for p in b]


def test_score_candidates_sorted_by_descending_total_score(draws_df):
    predictions = score_candidates(draws_df, total_predictions=10, random_seed=7)

    scores = [p.total_score for p in predictions]
    assert scores == sorted(scores, reverse=True)


def test_method_name_is_explainable():
    assert METHOD_NAME == "explainable"


def test_explainable_strategy_is_registered():
    model = get_model("explainable")

    assert model.__name__ == "generate"
