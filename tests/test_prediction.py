import pytest

from core.feature_score import Feature, ScoringEngine
from core.prediction import (
    CandidateGenerator,
    Prediction,
    PredictionGenerator,
    PredictionPipeline,
    prediction_to_record,
)


def sum_feature(weight=1.0):
    return Feature(name="sum_of_numbers", extractor=lambda t: sum(t.numbers), weight=weight)


class TestCandidateGenerator:
    def test_generates_requested_number_of_candidates(self):
        generator = CandidateGenerator(number_of_candidates=10, random_seed=1)

        candidates = generator.generate_candidates()

        assert len(candidates) == 10

    def test_candidates_have_valid_ranges_and_distinct_numbers(self):
        generator = CandidateGenerator(
            number_of_candidates=25,
            random_seed=2,
            numbers_count=5,
            max_number=69,
            special_max=26,
        )

        for ticket in generator.generate_candidates():
            assert len(ticket.numbers) == 5
            assert len(set(ticket.numbers)) == 5
            assert ticket.numbers == sorted(ticket.numbers)
            assert all(1 <= n <= 69 for n in ticket.numbers)
            assert 1 <= ticket.special <= 26
            assert ticket.method == "random_candidate"

    def test_same_seed_is_reproducible(self):
        a = CandidateGenerator(number_of_candidates=5, random_seed=42).generate_candidates()
        b = CandidateGenerator(number_of_candidates=5, random_seed=42).generate_candidates()

        assert [(t.numbers, t.special) for t in a] == [(t.numbers, t.special) for t in b]

    def test_different_seeds_produce_different_candidates(self):
        a = CandidateGenerator(number_of_candidates=5, random_seed=1).generate_candidates()
        b = CandidateGenerator(number_of_candidates=5, random_seed=2).generate_candidates()

        assert [(t.numbers, t.special) for t in a] != [(t.numbers, t.special) for t in b]

    def test_respects_custom_number_ranges(self):
        generator = CandidateGenerator(
            number_of_candidates=5,
            random_seed=3,
            numbers_count=3,
            max_number=10,
            special_max=4,
        )

        for ticket in generator.generate_candidates():
            assert len(ticket.numbers) == 3
            assert all(1 <= n <= 10 for n in ticket.numbers)
            assert 1 <= ticket.special <= 4


class TestPredictionGenerator:
    def test_cannot_be_instantiated_directly(self):
        with pytest.raises(TypeError):
            PredictionGenerator()


class TestPredictionPipeline:
    def test_is_a_prediction_generator(self):
        pipeline = PredictionPipeline(
            candidate_generator=CandidateGenerator(number_of_candidates=1, random_seed=1),
            scoring_engine=ScoringEngine(),
            top_n=1,
        )

        assert isinstance(pipeline, PredictionGenerator)

    def test_generate_returns_at_most_top_n_predictions(self):
        pipeline = PredictionPipeline(
            candidate_generator=CandidateGenerator(number_of_candidates=10, random_seed=5),
            scoring_engine=ScoringEngine(features=[sum_feature()]),
            top_n=3,
        )

        predictions = pipeline.generate()

        assert len(predictions) == 3
        assert all(isinstance(p, Prediction) for p in predictions)

    def test_generate_sorts_by_descending_total_score(self):
        pipeline = PredictionPipeline(
            candidate_generator=CandidateGenerator(number_of_candidates=20, random_seed=7),
            scoring_engine=ScoringEngine(features=[sum_feature()]),
            top_n=20,
        )

        scores = [p.total_score for p in pipeline.generate()]

        assert scores == sorted(scores, reverse=True)

    def test_generate_populates_prediction_fields(self):
        pipeline = PredictionPipeline(
            candidate_generator=CandidateGenerator(number_of_candidates=1, random_seed=9),
            scoring_engine=ScoringEngine(features=[sum_feature(weight=2.0)]),
            top_n=1,
            strategy_name="my_strategy",
        )

        prediction = pipeline.generate()[0]

        assert len(prediction.numbers) == 5
        assert 1 <= prediction.special_ball <= 26
        assert len(prediction.feature_scores) == 1
        assert prediction.feature_scores[0].feature_name == "sum_of_numbers"
        assert prediction.total_score == sum(prediction.numbers) * 2.0
        assert prediction.strategy == "my_strategy"
        assert prediction.metadata == {"method": "random_candidate"}

    def test_generate_with_no_features_gives_zero_scores(self):
        pipeline = PredictionPipeline(
            candidate_generator=CandidateGenerator(number_of_candidates=4, random_seed=11),
            scoring_engine=ScoringEngine(),
            top_n=4,
        )

        predictions = pipeline.generate()

        assert all(p.total_score == 0.0 for p in predictions)
        assert all(p.feature_scores == [] for p in predictions)

    def test_top_n_larger_than_candidate_pool_returns_all(self):
        pipeline = PredictionPipeline(
            candidate_generator=CandidateGenerator(number_of_candidates=2, random_seed=13),
            scoring_engine=ScoringEngine(features=[sum_feature()]),
            top_n=100,
        )

        assert len(pipeline.generate()) == 2


class TestPredictionToRecord:
    def test_includes_total_score_and_per_feature_score_columns(self):
        pipeline = PredictionPipeline(
            candidate_generator=CandidateGenerator(number_of_candidates=1, random_seed=1),
            scoring_engine=ScoringEngine(features=[sum_feature(weight=2.0)]),
            top_n=1,
        )
        prediction = pipeline.generate()[0]

        record = prediction_to_record(prediction)

        assert record["TotalScore"] == prediction.total_score
        assert record["SumOfNumbersScore"] == prediction.feature_scores[0].weighted_score
        assert record["numbers"] == prediction.numbers
        assert record["special"] == prediction.special_ball

    def test_method_column_is_the_prediction_strategy_not_metadata(self):
        prediction = Prediction(
            numbers=[1, 2, 3, 4, 5],
            special_ball=6,
            feature_scores=[],
            total_score=0.0,
            strategy="explainable",
            metadata={"method": "random_candidate"},
        )

        record = prediction_to_record(prediction)

        assert record["method"] == "explainable"

    def test_multiple_features_each_get_their_own_column(self):
        features = [
            Feature(name="pair", extractor=lambda t: 1.0, weight=1.0),
            Feature(name="hot", extractor=lambda t: 2.0, weight=1.0),
            Feature(name="odd_even", extractor=lambda t: 3.0, weight=1.0),
        ]
        pipeline = PredictionPipeline(
            candidate_generator=CandidateGenerator(number_of_candidates=1, random_seed=2),
            scoring_engine=ScoringEngine(features=features),
            top_n=1,
        )
        prediction = pipeline.generate()[0]

        record = prediction_to_record(prediction)

        assert record["PairScore"] == 1.0
        assert record["HotScore"] == 2.0
        assert record["OddEvenScore"] == 3.0
        assert record["TotalScore"] == 6.0
