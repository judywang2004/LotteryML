import pandas as pd


class MegaMillionsAdapter:

    def load(self):

        columns = [
            "Game",
            "Month",
            "Day",
            "Year",
            "N1",
            "N2",
            "N3",
            "N4",
            "N5",
            "SpecialBall",
            "Multiplier"
        ]

        df = pd.read_csv(
            "data/megamillions.csv",
            names=columns
        )

        df["DrawDate"] = pd.to_datetime(
            df[["Year", "Month", "Day"]]
        )

        df["Game"] = "MegaMillions"

        return df[
        [
        "Game",
        "DrawDate",
        "N1",
        "N2",
        "N3",
        "N4",
        "N5",
        "SpecialBall",
        "Multiplier",
    ]
]