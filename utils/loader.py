from adapters.megamillions import MegaMillionsAdapter
from adapters.powerball import PowerballAdapter

ADAPTERS = {
    "megamillions": MegaMillionsAdapter(),
    "powerball": PowerballAdapter(),
}


def load_lottery(game):

    game = game.lower()

    if game not in ADAPTERS:
        raise ValueError(f"Unsupported lottery: {game}")

    return ADAPTERS[game].load()