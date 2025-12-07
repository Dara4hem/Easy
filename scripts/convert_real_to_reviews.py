"""
Convert real G2 Postman reviews to synthetic Review schema for unified comparison.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="Convert real G2 reviews to Review schema")


@app.command()
def main(
    input_file: str = typer.Option(
        "data/real/postman_g2_reviews.jsonl",
        "--input",
        "-i",
        help="Path to real reviews JSONL file.",
    ),
    output_file: str = typer.Option(
        "data/real/postman_g2_as_reviews.jsonl",
        "--output",
        "-o",
        help="Path to output converted JSONL file.",
    ),
):
    """
    Convert real G2 reviews to the Review schema used for synthetic reviews.
    This allows unified quality analysis across synthetic and real datasets.
    """
    input_path = Path(input_file)
    if not input_path.exists():
        typer.echo(f"Input file not found: {input_path}")
        raise typer.Exit(code=1)

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    converted = []
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            real_review = json.loads(line)
            
            # Map to Review schema
            converted_review = {
                "review_id": real_review.get("review_id", "unknown"),
                "persona_id": "real_g2",  # Mark as real data
                "product": real_review.get("product", "Postman"),
                "rating": int(round(float(real_review.get("rating", 4.0)))),  # Round to int
                "title": real_review.get("title", ""),
                "body": real_review.get("body", ""),
                "created_at": _parse_date(real_review.get("review_date")),
                "source_model": "real:g2",
                "quality": {
                    "vocab_diversity": None,
                    "semantic_novelty": None,
                    "domain_realism": None,
                    "bias_flags": [],
                    "is_accepted": None,
                },
            }
            converted.append(converted_review)

    # Write output
    with output_path.open("w", encoding="utf-8") as f:
        for review in converted:
            f.write(json.dumps(review, ensure_ascii=False) + "\n")

    typer.echo(f"Converted {len(converted)} real reviews -> {output_path}")


def _parse_date(date_str: Optional[str]) -> str:
    """Parse review_date string into ISO datetime format."""
    if not date_str:
        return datetime.utcnow().isoformat()
    
    # Try parsing YYYY-MM-DD
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.isoformat()
    except (ValueError, TypeError):
        # Fallback to current time
        return datetime.utcnow().isoformat()


if __name__ == "__main__":
    app()

