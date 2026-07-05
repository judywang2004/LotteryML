from pathlib import Path
from datetime import datetime

import pandas as pd
import json


def save_predictions(game,
                     method,
                     predictions):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    folder = Path("output") / game / method

    folder.mkdir(parents=True,
                 exist_ok=True)

    csv_file = folder / f"{timestamp}.csv"

    txt_file = folder / f"{timestamp}.txt"

    json_file = folder / f"{timestamp}.json"

    pd.DataFrame(predictions).to_csv(
        csv_file,
        index=False
    )

    with open(json_file, "w") as f:

        json.dump(
            predictions,
            f,
            indent=4
        )

    with open(txt_file, "w") as f:

        f.write(
            f"{game}\n"
        )

        f.write(
            f"{method}\n\n"
        )

        for p in predictions:

            f.write(
                f"{p}\n"
            )

    print(csv_file)