"""
Generate comprehensive comparison report across multiple synthetic models and real data.
"""
from pathlib import Path
import json
from typing import Dict, List

import typer

from .io import load_reviews
from .quality import annotate_quality, QualitySummary

app = typer.Typer(help="Compare synthetic and real review quality")


@app.command()
def main(
    openai_file: str = typer.Option(
        "data/synthetic/dev_tools_openai_scored.jsonl",
        "--openai",
        help="Path to OpenAI synthetic reviews.",
    ),
    qwen_file: str = typer.Option(
        "data/synthetic/dev_tools_qwen30b_scored.jsonl",
        "--qwen",
        help="Path to Qwen3-30B synthetic reviews.",
    ),
    real_file: str = typer.Option(
        "data/real/postman_g2_as_reviews.jsonl",
        "--real",
        help="Path to real reviews (converted to Review schema).",
    ),
    output: str = typer.Option(
        "reports/comprehensive_comparison.md",
        "--output",
        "-o",
        help="Path to output comparison report.",
    ),
    expected_dist: str = typer.Option(
        "5:0.35,4:0.40,3:0.20,2:0.04,1:0.01",
        "--expected-dist",
        help="Expected rating distribution as comma-separated rating:prob pairs.",
    ),
):
    """
    Generate a comprehensive 3-way comparison report: OpenAI vs Qwen3-30B vs Real.
    """
    # Parse expected distribution
    expected_rating_dist = {}
    for pair in expected_dist.split(","):
        rating_str, prob_str = pair.split(":")
        expected_rating_dist[int(rating_str)] = float(prob_str)
    
    # Load datasets
    datasets: Dict[str, tuple[Path, List]] = {}
    
    openai_path = Path(openai_file)
    if openai_path.exists():
        datasets["OpenAI (gpt-4.1-mini)"] = (openai_path, load_reviews(openai_path))
    
    qwen_path = Path(qwen_file)
    if qwen_path.exists():
        datasets["Qwen3-30B (Ollama)"] = (qwen_path, load_reviews(qwen_path))
    
    real_path = Path(real_file)
    if real_path.exists():
        datasets["Real (G2)"] = (real_path, load_reviews(real_path))
    
    if len(datasets) < 2:
        typer.echo("Error: Need at least 2 datasets to compare.")
        raise typer.Exit(code=1)
    
    # Compute quality summaries
    summaries: Dict[str, QualitySummary] = {}
    for label, (path, reviews) in datasets.items():
        typer.echo(f"Analyzing {label}: {len(reviews)} reviews from {path}")
        summaries[label] = annotate_quality(reviews, expected_rating_dist=expected_rating_dist)
    
    # Generate report
    md_lines = _build_comparison_report(datasets, summaries, expected_rating_dist)
    
    # Write output
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(md_lines), encoding="utf-8")
    
    typer.echo(f"Comprehensive comparison report written -> {output_path}")


def _build_comparison_report(
    datasets: Dict[str, tuple[Path, List]],
    summaries: Dict[str, QualitySummary],
    expected_dist: Dict[int, float],
) -> List[str]:
    """Build the markdown comparison report."""
    lines = []
    
    lines.append("# Comprehensive Quality Comparison Report")
    lines.append("")
    lines.append("Comparing synthetic review quality across models and against real data.")
    lines.append("")
    
    # Dataset overview
    lines.append("## Datasets")
    lines.append("")
    for label, (path, reviews) in datasets.items():
        lines.append(f"- **{label}**: {len(reviews)} reviews from `{path}`")
    lines.append("")
    
    # Expected distribution
    lines.append("## Expected Rating Distribution (from config)")
    lines.append("")
    lines.append("| Rating | Expected % |")
    lines.append("|--------|-----------|")
    for rating in [5, 4, 3, 2, 1]:
        pct = expected_dist.get(rating, 0.0) * 100
        lines.append(f"| {rating}★ | {pct:.1f}% |")
    lines.append("")
    
    # Summary table
    lines.append("## Quality Metrics Comparison")
    lines.append("")
    lines.append("| Metric | " + " | ".join(summaries.keys()) + " |")
    lines.append("|--------|" + "|".join(["--------"] * len(summaries)) + "|")
    
    # Build rows
    metrics = [
        ("Vocab Diversity", lambda s: f"{s.avg_vocab_diversity:.3f}"),
        ("Semantic Novelty", lambda s: f"{s.avg_semantic_novelty:.3f}"),
        ("Domain Realism", lambda s: f"{s.avg_domain_realism:.3f}"),
        ("Rejection Rate", lambda s: f"{s.rejection_rate:.3f}"),
        ("High Rating Ratio (≥4★)", lambda s: f"{s.high_rating_ratio:.3f}"),
        ("Low Rating Ratio (≤2★)", lambda s: f"{s.low_rating_ratio:.3f}"),
        ("Rating Skew Score", lambda s: f"{s.rating_skew_score:.4f}"),
        ("Avg Sentiment", lambda s: f"{s.avg_sentiment_score:.3f}"),
    ]
    
    for metric_name, extractor in metrics:
        row = f"| {metric_name} | "
        row += " | ".join(extractor(summaries[label]) for label in summaries.keys())
        row += " |"
        lines.append(row)
    
    lines.append("")
    
    # Rating histograms
    lines.append("## Rating Distribution Comparison")
    lines.append("")
    lines.append("| Rating | " + " | ".join(summaries.keys()) + " |")
    lines.append("|--------|" + "|".join(["--------"] * len(summaries)) + "|")
    
    for rating in [5, 4, 3, 2, 1]:
        row = f"| {rating}★ | "
        counts = []
        for label in summaries.keys():
            count = summaries[label].rating_histogram.get(rating, 0)
            total = sum(summaries[label].rating_histogram.values())
            pct = (count / total * 100) if total > 0 else 0.0
            counts.append(f"{count} ({pct:.1f}%)")
        row += " | ".join(counts) + " |"
        lines.append(row)
    
    lines.append("")
    
    # Key insights
    lines.append("## Key Insights")
    lines.append("")
    
    # Identify best/worst per metric
    if len(summaries) >= 2:
        best_diversity = max(summaries.items(), key=lambda x: x[1].avg_vocab_diversity)
        best_realism = max(summaries.items(), key=lambda x: x[1].avg_domain_realism)
        lowest_rejection = min(summaries.items(), key=lambda x: x[1].rejection_rate)
        
        lines.append(f"- **Highest vocabulary diversity**: {best_diversity[0]} ({best_diversity[1].avg_vocab_diversity:.3f})")
        lines.append(f"- **Highest domain realism**: {best_realism[0]} ({best_realism[1].avg_domain_realism:.3f})")
        lines.append(f"- **Lowest rejection rate**: {lowest_rejection[0]} ({lowest_rejection[1].rejection_rate:.3f})")
        lines.append("")
        
        # Rating distribution alignment
        lines.append("### Rating Distribution Alignment")
        for label, summary in summaries.items():
            lines.append(f"- **{label}** rating skew score: `{summary.rating_skew_score:.4f}` (lower = closer to expected)")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Report generated by `python -m synthetic_reviews.compare_cli`*")
    
    return lines


if __name__ == "__main__":
    app()

