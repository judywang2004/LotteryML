from datetime import date

from core.ticket import Ticket


def test_ticket_holds_all_fields():
    ticket = Ticket(
        numbers=[4, 8, 15, 16, 23],
        special=42,
        score=0.87,
        method="frequency",
        draw_date=date(2026, 7, 18),
    )

    assert ticket.numbers == [4, 8, 15, 16, 23]
    assert ticket.special == 42
    assert ticket.score == 0.87
    assert ticket.method == "frequency"
    assert ticket.draw_date == date(2026, 7, 18)


def test_draw_date_defaults_to_none():
    ticket = Ticket(
        numbers=[1, 2, 3, 4, 5],
        special=10,
        score=0.5,
        method="hot",
    )

    assert ticket.draw_date is None


def test_tickets_with_same_fields_are_equal():
    kwargs = dict(
        numbers=[1, 2, 3, 4, 5],
        special=6,
        score=0.42,
        method="hot",
    )

    assert Ticket(**kwargs) == Ticket(**kwargs)


def test_tickets_with_different_scores_are_not_equal():
    base = dict(
        numbers=[1, 2, 3, 4, 5],
        special=6,
        method="hot",
    )

    assert Ticket(**base, score=0.1) != Ticket(**base, score=0.9)
