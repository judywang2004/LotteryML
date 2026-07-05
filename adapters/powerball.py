import pandas as pd


class PowerballAdapter:

    def load(self):

        df = pd.read_csv("data/powerball.csv")

        df["DrawDate"] = pd.to_datetime(df["Draw Date"])

        nums = df["Winning Numbers"].str.split(expand=True)

        df["N1"] = nums[0].astype(int)
        df["N2"] = nums[1].astype(int)
        df["N3"] = nums[2].astype(int)
        df["N4"] = nums[3].astype(int)
        df["N5"] = nums[4].astype(int)

        df["SpecialBall"] = nums[5].astype(int)

        df["Game"] = "PowerBall"

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