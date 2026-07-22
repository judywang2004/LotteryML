from utils.loader import load_lottery

from features.pair_frequency import calculate

# df = load_lottery("megamillions")
df = load_lottery("powerball")

pairs = calculate(df)

print(pairs.most_common(20))