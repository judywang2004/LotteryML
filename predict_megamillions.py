import pandas as pd

cols = [
    "Game",
    "Month",
    "Day",
    "Year",
    "N1",
    "N2",
    "N3",
    "N4",
    "N5",
    "MegaBall",
    "Multiplier"
]

df = pd.read_csv(
    "data/megamillions.csv",
    names=cols
)

print(df.head())