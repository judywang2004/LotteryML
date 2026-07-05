import re
import json
import csv
import sys
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
import os
import time

URL = "https://www.palottery.pa.gov/Draw-Games/Winning-Numbers-History.aspx"
OUTPUT_CSV = "powerball_2025_2026.csv"
OUTPUT_JSON = "powerball_2025_2026.json"
YEARS = {2025, 2026}

num_regex = re.compile(r"\b(\d{1,2})\b")
date_regex = re.compile(r"([A-Za-z]+\s+\d{1,2},\s*\d{4})")

import requests
import csv
import json
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import io

CATALOG_URL = "https://catalog.data.gov/dataset/lottery-powerball-winning-numbers-beginning-2020"
OUTPUT_CSV = "powerball_2025_2026.csv"
OUTPUT_JSON = "powerball_2025_2026.json"
YEARS = {2025, 2026}


def find_resource_urls(catalog_html):
    """Parse the catalog page HTML and return candidate CSV/JSON resource URLs."""
    soup = BeautifulSoup(catalog_html, "html.parser")
    links = set()
    # Look for <a> tags with hrefs ending with .csv/.json or containing common data host domains
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".csv") or href.lower().endswith(".json"):
            links.add(href)
        # common data host
        import re
        import requests
        import csv
        import json
        from datetime import datetime
        from pathlib import Path
        from bs4 import BeautifulSoup
        import io

        CATALOG_URL = "https://catalog.data.gov/dataset/lottery-powerball-winning-numbers-beginning-2020"
        OUTPUT_CSV = "powerball_2025_2026.csv"
        OUTPUT_JSON = "powerball_2025_2026.json"
        YEARS = {2025, 2026}


        def find_resource_urls(catalog_html):
            """Parse the catalog page HTML and return candidate CSV/JSON resource URLs."""
            soup = BeautifulSoup(catalog_html, "html.parser")
            links = set()
            # Look for <a> tags with hrefs ending with .csv/.json or containing common data host domains
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.lower().endswith(".csv") or href.lower().endswith(".json"):
                    links.add(href)
                # common data host
                if any(d in href for d in ("data.ny.gov", "data.gov", "socrata", "ckan")):
                    links.add(href)
            return list(links)


        def download_text(url):
            headers = {"User-Agent": "python-requests/2.0"}
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            return r.text


        def download_file_stream(url, out_path: Path):
            """Download a URL to out_path using streaming and show simple progress."""
            headers = {"User-Agent": "python-requests/2.0"}
            with requests.get(url, headers=headers, stream=True, timeout=60) as r:
                r.raise_for_status()
                total = r.headers.get("content-length")
                if total is not None:
                    total = int(total)
                written = 0
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with out_path.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if not chunk:
                            continue
                        f.write(chunk)
                        written += len(chunk)
                        if total:
                            pct = written * 100 // total
                            print(f"Downloading {out_path.name}: {pct}% ({written}/{total} bytes)", end="\r")
                if total:
                    print(f"\nDownloaded {out_path.name}: {written}/{total} bytes")
                else:
                    print(f"Downloaded {out_path.name}: {written} bytes")


        def parse_csv_text(text):
            f = io.StringIO(text)
            reader = csv.DictReader(f)
            rows = [row for row in reader]
            return rows


        def normalize_and_filter(rows):
            """Normalize various dataset column names and extract draws for YEARS."""
            results = []
            for r in rows:
                # Find date column
                date_val = None
                for k in r:
                    if "date" in k.lower():
                        date_val = r[k]
                        break
                if not date_val:
                    # try other common names
                    for k in r:
                        if "draw" in k.lower() and "date" in k.lower():
                            date_val = r[k]
                            break
                if not date_val:
                    continue
                # parse date
                date_obj = None
                for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"):
                    try:
                        date_obj = datetime.strptime(date_val.strip(), fmt)
                        break
                    except Exception:
                        continue
                if not date_obj:
                    continue
                if date_obj.year not in YEARS:
                    continue

                # Find numbers: either a single 'winning numbers' field or multiple columns
                whites = []
                power = None
                # Try single combined field
                for k in r:
                    if "winning" in k.lower() or "numbers" in k.lower():
                        val = r[k].strip()
                        # split on space/comma/semicolon
                        parts = [p for p in re.split(r"[ ,;]+", val) if p]
                        nums = []
                        for p in parts:
                            try:
                                nums.append(int(p))
                            except Exception:
                                pass
                        if len(nums) >= 6:
                            whites = nums[:5]
                            power = nums[5]
                        elif len(nums) > 0:
                            whites = nums[:-1]
                            power = nums[-1]
                        break

                # Try separate columns for balls
                if not whites:
                    ball_cols = []
                    for k in r:
                        if any(x in k.lower() for x in ("ball", "white", "w1", "w2", "w3", "w4", "w5", "number1")):
                            ball_cols.append(k)
                    # sort by column name to try to get order
                    ball_cols = sorted(ball_cols)
                    nums = []
                    for k in ball_cols:
                        v = r.get(k, "").strip()
                        try:
                            nums.append(int(v))
                        except Exception:
                            pass
                    if nums:
                        if len(nums) >= 6:
                            whites = nums[:5]
                            power = nums[5]
                        elif len(nums) > 0:
                            whites = nums[:-1]
                            power = nums[-1]

                results.append({
                    "date": date_obj.strftime("%Y-%m-%d"),
                    "white_balls": whites,
                    "power_ball": power,
                    "raw_row": r,
                })
            return results


        def save_outputs(draws, out_dir: Path):
            csv_file = out_dir / OUTPUT_CSV
            json_file = out_dir / OUTPUT_JSON
            # write CSV
            with csv_file.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["date", "white_balls", "power_ball"])
                for d in sorted(draws, key=lambda x: x["date"]):
                    writer.writerow([d["date"], " ".join(map(str, d["white_balls"])), d["power_ball"]])
            # write JSON
            with json_file.open("w", encoding="utf-8") as f:
                json.dump(sorted(draws, key=lambda x: x["date"]), f, ensure_ascii=False, indent=2)
            print(f"Saved {len(draws)} draws to {csv_file} and {json_file}")


        def main():
            out_dir = Path.cwd()
            # Allow overriding the direct data URL (e.g. Socrata CSV) via DATA_URL env var
            DATA_URL = os.environ.get("DATA_URL")
            if DATA_URL:
                resources = [DATA_URL]
            else:
                print(f"Fetching catalog page: {CATALOG_URL}")
                html = download_text(CATALOG_URL)
                resources = find_resource_urls(html)
            if not resources:
                print("No direct CSV/JSON links found on catalog page. Will attempt to search page text for data links.")
                # fallback: look for any absolute URLs in the HTML
                import re as _re
                candidates = set(_re.findall(r'https?://[^\"\']+\.(?:csv|json)', html, flags=_re.I))
                resources = list(candidates)
            if not resources:
                print("No machine-readable resources found on the catalog page. Please provide the direct CSV/JSON URL.")
                return

            print("Found candidate resources:")
            for r in resources:
                print(" -", r)

            # Try resources in order until we get parsable CSV
            all_draws = []
            for r in resources:
                try:
                    print(f"Downloading resource: {r}")
                    # If link looks like a CSV download, stream-save it to disk first
                    target_file = out_dir / "ny_rows.csv"
                    try:
                        download_file_stream(r, target_file)
                        with target_file.open("r", encoding="utf-8") as fh:
                            txt = fh.read()
                    except Exception:
                        # fallback to text download
                        txt = download_text(r)

                    rows = parse_csv_text(txt)
                    draws = normalize_and_filter(rows)
                    if draws:
                        all_draws.extend(draws)
                        break
                except Exception as e:
                    print(f"Failed to download/parse {r}: {e}")

            if not all_draws:
                print("No draws extracted from candidate resources. Try providing direct CSV URL or run the Playwright scraper for the original site.")
                return

            save_outputs(all_draws, out_dir)


        if __name__ == '__main__':
            main()
