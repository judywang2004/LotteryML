import argparse

#
# 导入模型
#

import models.hot_numbers
import models.frequency
import strategies.pair
import strategies.explainable

from models.registry import (
    get_model,
    available_models
)

from utils.writer import save_predictions


parser = argparse.ArgumentParser()

parser.add_argument(
    "--game",
    required=True
)

parser.add_argument(
    "--method",
    required=True
)

args = parser.parse_args()


predict = get_model(args.method)

predictions = predict(args.game)

save_predictions(
    game=args.game,
    method=args.method,
    predictions=predictions
)

print("Available Models:")
print(available_models())