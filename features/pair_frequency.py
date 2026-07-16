from collections import Counter
from itertools import combinations


def calculate(df):

    counter = Counter()

    for _, row in df.iterrows():

        nums = sorted([
            row.N1,
            row.N2,
            row.N3,
            row.N4,
            row.N5
        ])

        for pair in combinations(nums, 2):
            counter[pair] += 1

    return counter