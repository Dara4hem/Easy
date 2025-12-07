from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List, Dict, Set

from .generation import Review


WORD_RE = re.compile(r"\w+")


def tokenize(text: str) -> List[str]:
    return [w.lower() for w in WORD_RE.findall(text)]


def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


@dataclass
class QualitySummary:
    avg_vocab_diversity: float
    avg_semantic_novelty: float
    avg_domain_realism: float
    rejection_rate: float
    rating_histogram: Dict[int, int]
    # Bias/skew metrics
    high_rating_ratio: float  # % of ratings >= 4
    low_rating_ratio: float   # % of ratings <= 2
    rating_skew_score: float  # KL-like divergence from expected distribution
    avg_sentiment_score: float  # Simple sentiment heuristic


def _compute_sentiment_score(token_set: Set[str]) -> float:
    """
    Simple sentiment heuristic: (#positive - #negative) / total
    Returns a value roughly in [-1, 1].
    """
    positive_words = {
        "great", "excellent", "good", "love", "best", "perfect", "amazing",
        "easy", "helpful", "fast", "reliable", "powerful", "smooth", "efficient"
    }
    negative_words = {
        "bad", "poor", "worst", "hate", "terrible", "awful", "slow",
        "bug", "crash", "fail", "broken", "unusable", "frustrating", "confusing"
    }
    pos_count = len(token_set & positive_words)
    neg_count = len(token_set & negative_words)
    total = len(token_set)
    return (pos_count - neg_count) / total if total > 0 else 0.0


def annotate_quality(
    reviews: List[Review],
    domain_keywords: Iterable[str] | None = None,
    expected_rating_dist: Dict[int, float] | None = None,
) -> QualitySummary:
    if domain_keywords is None:
        domain_keywords = {
            "api",
            "endpoint",
            "request",
            "response",
            "debug",
            "debugging",
            "auth",
            "token",
            "rest",
            "http",
            "headers",
            "payload",
            "json",
            "postman",
            "insomnia",
            "hoppscotch",
            "ci",
            "pipeline",
            "test",
            "testing",
        }
    else:
        domain_keywords = {k.lower() for k in domain_keywords}

    seen_token_sets: List[Set[str]] = []
    vocab_divs: List[float] = []
    novelties: List[float] = []
    realism_scores: List[float] = []
    sentiment_scores: List[float] = []
    rejections = 0
    rating_hist: Dict[int, int] = {}

    for r in reviews:
        tokens = tokenize(r.body)
        token_set = set(tokens)
        total_tokens = len(tokens)
        unique_tokens = len(token_set)

        vocab_div = (unique_tokens / total_tokens) if total_tokens > 0 else 0.0

        if seen_token_sets:
            max_j = max(jaccard(token_set, prev) for prev in seen_token_sets)
        else:
            max_j = 0.0
        novelty = 1.0 - max_j

        if domain_keywords:
            overlap = len(token_set & domain_keywords)
            realism = overlap / len(domain_keywords)
        else:
            realism = 0.0

        flags: List[str] = []

        if total_tokens < 30:
            flags.append("too_short")

        if max_j > 0.8:
            flags.append("high_overlap")

        if realism < 0.05:
            flags.append("low_domain_realism")

        negative_words = {"bug", "crash", "fail", "broken", "unusable"}
        if r.rating >= 4 and (token_set & negative_words):
            flags.append("rating_text_mismatch")

        positive_hype = {"perfect", "flawless", "amazing", "incredible"}
        if r.rating <= 2 and (token_set & positive_hype):
            flags.append("rating_text_mismatch")

        is_accepted = len(flags) == 0

        r.quality.vocab_diversity = vocab_div
        r.quality.semantic_novelty = novelty
        r.quality.domain_realism = realism
        r.quality.bias_flags = flags
        r.quality.is_accepted = is_accepted

        # Compute sentiment
        sentiment = _compute_sentiment_score(token_set)
        sentiment_scores.append(sentiment)
        
        seen_token_sets.append(token_set)
        vocab_divs.append(vocab_div)
        novelties.append(novelty)
        realism_scores.append(realism)
        if not is_accepted:
            rejections += 1

        rating_hist[r.rating] = rating_hist.get(r.rating, 0) + 1

    n = len(reviews) or 1
    
    # Compute bias/skew metrics
    high_rating_count = sum(1 for r in reviews if r.rating >= 4)
    low_rating_count = sum(1 for r in reviews if r.rating <= 2)
    high_rating_ratio = high_rating_count / n
    low_rating_ratio = low_rating_count / n
    
    # Compute rating skew score (simplified KL divergence if expected dist provided)
    rating_skew = 0.0
    if expected_rating_dist:
        # Normalize actual histogram
        actual_dist = {k: v / n for k, v in rating_hist.items()}
        # Simple squared difference as skew metric
        for rating in [1, 2, 3, 4, 5]:
            expected = expected_rating_dist.get(rating, 0.0)
            actual = actual_dist.get(rating, 0.0)
            rating_skew += (actual - expected) ** 2
    
    summary = QualitySummary(
        avg_vocab_diversity=sum(vocab_divs) / n if vocab_divs else 0.0,
        avg_semantic_novelty=sum(novelties) / n if novelties else 0.0,
        avg_domain_realism=sum(realism_scores) / n if realism_scores else 0.0,
        rejection_rate=rejections / n,
        rating_histogram=rating_hist,
        high_rating_ratio=high_rating_ratio,
        low_rating_ratio=low_rating_ratio,
        rating_skew_score=rating_skew,
        avg_sentiment_score=sum(sentiment_scores) / n if sentiment_scores else 0.0,
    )
    return summary
