from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .generation import Review


def load_reviews(path: str | Path) -> List[Review]:
    """
    Load reviews from a JSONL file into a list[Review].
    """
    p = Path(path)
    reviews: List[Review] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            reviews.append(Review.model_validate(data))
    return reviews


def save_reviews(path: str | Path, reviews: List[Review]) -> None:
    """
    Save reviews (with quality fields) back to JSONL.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for r in reviews:
            f.write(json.dumps(r.model_dump(mode="json"), ensure_ascii=False) + "\n")
