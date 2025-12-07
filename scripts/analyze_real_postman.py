import json
from pathlib import Path
from statistics import mean

PATH = Path("data/real/postman_g2_reviews.jsonl")

def main():
    ratings = []
    lengths = []

    with PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            ratings.append(float(r["rating"]))
            lengths.append(len(r["body"].split()))

    print(f"Num reviews: {len(ratings)}")
    print(f"Avg rating: {mean(ratings):.2f}")
    print(f"Min rating: {min(ratings)}, Max rating: {max(ratings)}")
    print(f"Avg review length (words): {mean(lengths):.1f}")

if __name__ == "__main__":
    main()
