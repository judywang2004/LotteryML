from utils.loader import load_lottery

for game in ["megamillions", "powerball"]:

    print("=" * 60)
    print(game)

    df = load_lottery(game)

    print(df.head())

    print(df.columns.tolist())