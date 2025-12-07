from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import typer

app = typer.Typer(help="Scrape G2 Postman review detail pages into JSONL")


@dataclass
class RealReview:
    review_id: str
    product: str
    platform: str
    source_url: str
    rating: Optional[float] = None
    title: Optional[str] = None
    body: Optional[str] = None
    reviewer_role: Optional[str] = None
    review_date: Optional[str] = None  # ISO string: YYYY-MM-DD


def _extract_text(node) -> str:
    if not node:
        return ""
    return " ".join(node.stripped_strings)


def _guess_review_id(url: str) -> str:
    """
    Build a stable review_id from the G2 slug, e.g.
    /products/postman/reviews/postman-review-12000022 -> g2_postman-review-12000022
    """
    path = urlparse(url).path.rstrip("/")
    slug = path.split("/")[-1]  # postman-review-12000022
    return f"g2_{slug}"


def _parse_rating(soup: BeautifulSoup) -> Optional[float]:
    # Try itemprop="ratingValue"
    meta = soup.find(attrs={"itemprop": "ratingValue"})
    if meta:
        # Can be <meta content="5"> or <span>5</span>
        val = meta.get("content") or meta.get_text(strip=True)
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    # Fallback: search for something like "4.5 out of 5"
    for possible in soup.find_all(string=True):
        text = possible.strip()
        if "out of 5" in text:
            num = text.split("out of 5")[0].strip()
            try:
                return float(num)
            except ValueError:
                continue

    return None


def _parse_review_date(soup: BeautifulSoup) -> Optional[str]:
    # Often wrapped in <time> tag
    time_tag = soup.find("time")
    if time_tag and time_tag.get("datetime"):
        # If there's a proper datetime attribute
        raw = time_tag["datetime"]
        try:
            # Try to parse and normalize to YYYY-MM-DD
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt.date().isoformat()
        except Exception:
            pass

    if time_tag:
        # Fallback: parse text like "12/4/2025"
        text = time_tag.get_text(strip=True)
        for fmt in ("%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y"):
            try:
                dt = datetime.strptime(text, fmt)
                return dt.date().isoformat()
            except ValueError:
                continue

    return None


def _parse_reviewer_role(soup: BeautifulSoup) -> Optional[str]:
    # Try a few common selectors for job title
    selectors = [
        '[itemprop="jobTitle"]',
        '[data-test="reviewer-job-title"]',
    ]
    for sel in selectors:
        node = soup.select_one(sel)
        if node:
            text = _extract_text(node)
            if text:
                return text
    return None


def _parse_title(soup: BeautifulSoup) -> Optional[str]:
    # G2 often uses an h1 or h2 for the review headline
    candidates = [
        'h1[data-test="review-headline"]',
        'h2[data-test="review-headline"]',
        "h1",
        "h2",
    ]
    for sel in candidates:
        node = soup.select_one(sel)
        text = _extract_text(node)
        if text:
            return text
    return None


def _parse_body(soup: BeautifulSoup) -> Optional[str]:
    """
    Try to collect Q&A sections like:
      - What do you like best about Postman?
      - What do you dislike about Postman?
      - What problems is Postman solving...
    and join them into a single body text.
    """
    parts = []

    # Many review sites use Q/A blocks. We'll try generic patterns first.
    # These selectors might need tweaking if G2 changes their DOM.
    question_selectors = [
        '[data-test="review-question"]',
        '[data-test="reviewQuestion"]',
    ]

    answer_selectors = [
        '[data-test="review-answer"]',
        '[data-test="reviewAnswer"]',
    ]

    questions = []
    for sel in question_selectors:
        questions.extend(soup.select(sel))

    if questions:
        for q in questions:
            q_text = _extract_text(q)
            # Find nearest following answer block
            ans = None
            # First: look for a sibling that matches answer selectors
            sib = q.find_next_sibling()
            while sib is not None and ans is None:
                for ans_sel in answer_selectors:
                    cand = sib.select_one(ans_sel) if hasattr(sib, "select_one") else None
                    if cand:
                        ans = cand
                        break
                sib = sib.find_next_sibling() if ans is None else None

            a_text = _extract_text(ans) if ans else ""
            if q_text and a_text:
                parts.append(f"{q_text}\n{a_text}")

    if parts:
        return "\n\n".join(parts)

    # Fallback: try to grab the main article/container text
    for sel in [
        "article",
        '[data-test="review-body"]',
        '[data-test="reviewBody"]',
    ]:
        node = soup.select_one(sel)
        if node:
            text = _extract_text(node)
            if text:
                return text

    # Last resort: entire page text (can be noisy)
    text = _extract_text(soup.body)
    return text or None


def scrape_single_review(url: str, product: str = "Postman") -> RealReview:
    review_id = _guess_review_id(url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/129.0 Safari/537.36"
        )
    }

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    title = _parse_title(soup)
    rating = _parse_rating(soup)
    body = _parse_body(soup)
    reviewer_role = _parse_reviewer_role(soup)
    review_date = _parse_review_date(soup)

    return RealReview(
        review_id=review_id,
        product=product,
        platform="g2",
        source_url=url,
        rating=rating,
        title=title,
        body=body,
        reviewer_role=reviewer_role,
        review_date=review_date,
    )


@app.command()
def main(
    urls_file: str = typer.Option(
        ...,
        "--urls-file",
        "-u",
        help="Path to a text file containing one G2 Postman review URL per line.",
    ),
    output: str = typer.Option(
        "data/real/postman_g2_reviews.jsonl",
        "--output",
        "-o",
        help="Path to output JSONL file.",
    ),
    product: str = typer.Option(
        "Postman",
        "--product",
        "-p",
        help="Product name to store in the JSON (default: Postman).",
    ),
):
    """
    Read a list of G2 review URLs and write parsed reviews to JSONL.
    """
    urls_path = Path(urls_file)
    if not urls_path.exists():
        typer.echo(f"URLs file not found: {urls_path}")
        raise typer.Exit(code=1)

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    urls: list[str] = []
    with urls_path.open("r", encoding="utf-8") as f:
        for line in f:
            u = line.strip()
            if not u or u.startswith("#"):
                continue
            urls.append(u)

    typer.echo(f"Found {len(urls)} URLs in {urls_path}")

    reviews: list[RealReview] = []
    for idx, url in enumerate(urls, start=1):
        typer.echo(f"[{idx}/{len(urls)}] Fetching {url} ...")
        try:
            review = scrape_single_review(url, product=product)
            reviews.append(review)
        except Exception as e:
            typer.echo(f"  !! Error scraping {url}: {e}")

    with out_path.open("w", encoding="utf-8") as f:
        for r in reviews:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")

    typer.echo(f"Wrote {len(reviews)} reviews -> {out_path}")


if __name__ == "__main__":
    app()
