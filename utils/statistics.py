from collections import Counter


def number_frequency(df):

    counter = Counter()

    for _, row in df.iterrows():

        counter.update([
            row.N1,
            row.N2,
            row.N3,
            row.N4,
            row.N5
        ])

    return counter


def special_frequency(df):

    counter = Counter()

    counter.update(df.SpecialBall)

    return counter