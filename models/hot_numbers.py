import random

from utils.loader import load_lottery
from utils.statistics import (
    number_frequency,
    special_frequency
)

METHOD_NAME = "hot"
from models.registry import register

def predict(game,
            total_predictions=20):

    df = load_lottery(game)

    freq = number_frequency(df)

    mega = special_frequency(df)

    nums = list(freq.keys())

    weights = list(freq.values())

    mega_nums = list(mega.keys())

    mega_weights = list(mega.values())

    predictions = []

    while len(predictions) < total_predictions:

        picks = []

        while len(picks) < 5:

            n = random.choices(
                nums,
                weights
            )[0]

            if n not in picks:
                picks.append(n)

        picks.sort()

        mb = random.choices(
            mega_nums,
            mega_weights
        )[0]

        predictions.append({

            "numbers": picks,

            "special": mb

        })

    return predictions

register(METHOD_NAME,predict)