import random

from utils.loader import load_lottery
from utils.statistics import (
    number_frequency,
    special_frequency
)

METHOD_NAME = "frequency"
from models.registry import register

def predict(game,
            total_predictions=20):

    df = load_lottery(game)

    freq = number_frequency(df)

    mega = special_frequency(df)

    total = sum(freq.values())

    probabilities = {}

    for n, c in freq.items():
        probabilities[n] = c / total

    numbers = list(probabilities.keys())

    weights = list(probabilities.values())

    mega_total = sum(mega.values())

    mega_prob = {}

    for n, c in mega.items():
        mega_prob[n] = c / mega_total

    mega_numbers = list(mega_prob.keys())

    mega_weights = list(mega_prob.values())

    predictions = []

    while len(predictions) < total_predictions:

        picks = []

        while len(picks) < 5:

            n = random.choices(
                numbers,
                weights
            )[0]

            if n not in picks:
                picks.append(n)

        picks.sort()

        mb = random.choices(
            mega_numbers,
            mega_weights
        )[0]

        predictions.append({

            "numbers": picks,

            "special": mb,

            "method": "Frequency"

        })

    return predictions


register(METHOD_NAME, predict)