import json

def get_config(game):

    with open("config/lotteries.json") as f:
        data = json.load(f)

    return data[game.lower()]