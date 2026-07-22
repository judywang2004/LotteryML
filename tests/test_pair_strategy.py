import pandas as pd
import pytest

from core.ticket import Ticket
from models.registry import get_model
from strategies.pair import METHOD_NAME, predict


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


def test_predict_returns_tickets(draws_df):
    tickets = predict(draws_df, total_predictions=3)

    assert len(tickets) == 3
    assert all(isinstance(t, Ticket) for t in tickets)


def test_predict_seeds_tickets_with_most_frequent_pair_first(draws_df):
    tickets = predict(draws_df, total_predictions=1)

    assert tickets[0].numbers[:2] == [1, 2]
    assert tickets[0].score == 3.0
    assert tickets[0].method == "pair"


def test_predict_tickets_have_valid_shape(draws_df):
    for ticket in predict(draws_df, total_predictions=4):
        assert len(ticket.numbers) == 5
        assert len(set(ticket.numbers)) == 5
        assert ticket.numbers == sorted(ticket.numbers)
        assert 1 <= ticket.special <= 8

def test_predict_respects_total_predictions_upper_bound(draws_df):
    tickets = predict(draws_df, total_predictions=100)

    assert len(tickets) <= 100


def test_method_name_is_pair():
    assert METHOD_NAME == "pair"


def test_pair_strategy_is_registered_under_pair():
    model = get_model("pair")

    assert model.__name__ == "generate"
