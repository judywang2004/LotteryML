"""Predict Powerball candidate combinations from `ny_rows.csv` using frequency heuristics.

This script reads `ny_rows.csv` (downloaded from data.ny.gov), computes frequency
of white balls (1-69) and power balls (1-26), and outputs 5 suggested combinations
based on weighted sampling from the most frequent numbers.

Disclaimer: Lotteries are random. These are heuristic suggestions with no guarantee.
"""
import argparse
import csv
import random
from collections import Counter
from pathlib import Path
from datetime import datetime
import json
from typing import List, Tuple

DATA_FILE = Path('megamillions.csv')
NUM_SUGGESTIONS = 5
TOP_WHITES = 20  # consider top-N white balls for sampling
TOP_POWERS = 6   # consider top-N power balls for sampling
SEED = 42


def parse_date(s: str):
    for fmt in ('%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None


def load_rows(path: Path) -> List[Tuple[datetime, List[int], int]]:
    if not path.exists():
        raise SystemExit(f"Data file not found: {path}. Please run the downloader first.")
    rows = []
    with path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            # parse date if available
            date_field = None
            for k in r:
                if 'draw' in k.lower() and 'date' in k.lower():
                    date_field = r[k]
                    break
            draw_date = parse_date(date_field) if date_field else None

            # Expect "Winning Numbers" column
            wn = r.get('Winning Numbers') or r.get('winning numbers') or r.get('Winning numbers')
            if not wn:
                # try alternative column names
                for k in r:
                    if 'win' in k.lower() and 'number' in k.lower():
                        wn = r[k]
                        break
            if not wn:
                continue
            parts = wn.strip().split()
            if len(parts) < 6:
                continue
            try:
                whites = [int(p) for p in parts[:5]]
                power = int(parts[5])
            except Exception:
                continue
            rows.append((draw_date, whites, power))
    # sort by date if available (None dates will be placed at the beginning)
    try:
        rows.sort(key=lambda x: x[0] or datetime.min)
    except Exception:
        pass
    return rows


def compute_frequencies(rows, recent: int = None):
    """
    rows: List of (date, whites, power). If recent is provided, only use the last `recent` rows.
    """
    if recent is not None and recent > 0:
        rows = rows[-recent:]
    white_counter = Counter()
    power_counter = Counter()
    for _date, whites, power in rows:
        white_counter.update(whites)
        power_counter.update([power])
    return white_counter, power_counter


def weighted_sample(numbers, weights, k, rng: random.Random):
    # numbers: list of items, weights: matching list of non-negative weights
    total = sum(weights)
    if total <= 0:
        return sorted(rng.sample(numbers, k))
    nums = list(numbers)
    wts = list(weights)
    chosen = []
    for _ in range(min(k, len(nums))):
        r = rng.random() * sum(wts)
        cum = 0.0
        for i, (n, w) in enumerate(zip(nums, wts)):
            cum += w
            if r <= cum:
                chosen.append(n)
                # remove selected
                nums.pop(i)
                wts.pop(i)
                break
    return sorted(chosen)


def generate_suggestions(white_counter, power_counter, count: int, rng: random.Random,
                         top_whites: int = TOP_WHITES, top_powers: int = TOP_POWERS):
    white_items = [n for n, _ in white_counter.most_common(top_whites)]
    white_weights = [white_counter[n] for n in white_items]
    power_items = [n for n, _ in power_counter.most_common(top_powers)]
    power_weights = [power_counter[n] for n in power_items]

    suggestions = []
    for i in range(count):
        whites = weighted_sample(white_items, white_weights, 5, rng)
        power = rng.choices(power_items, weights=power_weights, k=1)[0]
        suggestions.append((whites, power))
    return suggestions


def main():
    parser = argparse.ArgumentParser(description="Generate Powerball suggestions from historical CSV")
    parser.add_argument('--data', '-d', default=str(DATA_FILE), help='CSV data file (default: ny_rows.csv)')
    parser.add_argument('--recent', '-r', type=int, default=None,
                        help='Use only the most recent N draws to compute frequencies')
    parser.add_argument('--seed', '-s', type=int, action='append', default=None,
                        help='Random seed to use; may be repeated to generate multiple sets')
    parser.add_argument('--count', '-c', type=int, default=NUM_SUGGESTIONS,
                        help='Number of suggestions to generate per seed')
    parser.add_argument('--top-whites', type=int, default=TOP_WHITES,
                        help='Consider top-N white balls for sampling')
    parser.add_argument('--top-powers', type=int, default=TOP_POWERS,
                        help='Consider top-N power balls for sampling')
    args = parser.parse_args()

    data_path = Path(args.data)
    rows = load_rows(data_path)
    if not rows:
        raise SystemExit('No valid rows parsed from data file')

    seeds = args.seed or [SEED]
    for seed in seeds:
        white_counter, power_counter = compute_frequencies(rows, recent=args.recent)
        rng = random.Random(seed)
        suggestions = generate_suggestions(white_counter, power_counter, args.count, rng,
                                           top_whites=args.top_whites, top_powers=args.top_powers)

        print(f"Suggestions for seed={seed} (white balls sorted):")
        for whites, power in suggestions:
            print(f"Whites: {' '.join(str(w).zfill(2) for w in whites)}  |  Powerball: {str(power).zfill(2)}")

        # Save suggestions with timestamped filenames including seed
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_out = Path(f'predictions_powerball_seed{seed}_{ts}.csv')
        json_out = Path(f'predictions_powerball_seed{seed}_{ts}.json')

        with csv_out.open('w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['white_balls', 'power_ball', 'seed', 'recent'])
            for whites, power in suggestions:
                writer.writerow([' '.join(str(w).zfill(2) for w in whites), str(power).zfill(2), seed, args.recent or 'all'])

        with json_out.open('w', encoding='utf-8') as f:
            json.dump([
                {'white_balls': whites, 'power_ball': power, 'seed': seed, 'recent': args.recent or 'all'} for whites, power in suggestions
            ], f, ensure_ascii=False, indent=2)

        print(f"Saved predictions to {csv_out} and {json_out}\n")


if __name__ == '__main__':
    main()
