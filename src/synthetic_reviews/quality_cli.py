from pathlib import Path
import json

import typer

from .io import load_reviews
from .quality import annotate_quality, QualitySummary


def main(
    synthetic: str = typer.Option(
        ...,
        help="Path to synthetic *scored* JSONL file (e.g. dev_tools_qwen30b_scored.jsonl).",
    ),
    real: str = typer.Option(
        None,
        help="Optional path to real reviews JSONL file (same schema as synthetic).",
    ),
    output: str = typer.Option(
        "reports/dev_tools_quality.md",
        help="Path to output Markdown report.",
    ),
    label: str = typer.Option(
        "qwen30b",
        help="Label/name of the synthetic model/dataset (e.g. openai, qwen30b).",
    ),
):
    """
    Generate a Markdown quality report comparing synthetic (and optionally real) reviews.
    """
    syn_path = Path(synthetic)
    if not syn_path.exists():
        typer.echo(f"Synthetic file not found: {syn_path}")
        raise typer.Exit(code=1)

    syn_reviews = load_reviews(syn_path)
    syn_summary = annotate_quality(syn_reviews)

    real_summary = None
    real_path = None
    if real:
        real_path = Path(real)
        if not real_path.exists():
            typer.echo(f"Real file not found: {real_path}")
            raise typer.Exit(code=1)
        real_reviews = load_reviews(real_path)
        real_summary = annotate_quality(real_reviews)

    md_lines: list[str] = []

    md_lines.append(f"# Quality Report – {label}")
    md_lines.append("")
    md_lines.append("## Inputs")
    md_lines.append("")
    md_lines.append(f"- Synthetic file: `{syn_path}`")
    if real_path:
        md_lines.append(f"- Real file: `{real_path}`")
    md_lines.append("")

    # synthetic summary
    md_lines.append("## Synthetic Summary")
    md_lines.append("")
    md_lines.append("### Diversity Metrics")
    md_lines.append(f"- Average vocab diversity: `{syn_summary.avg_vocab_diversity:.3f}`")
    md_lines.append(f"- Average semantic novelty: `{syn_summary.avg_semantic_novelty:.3f}`")
    md_lines.append(f"- Average domain realism: `{syn_summary.avg_domain_realism:.3f}`")
    md_lines.append("")
    md_lines.append("### Quality & Bias Metrics")
    md_lines.append(f"- Rejection rate: `{syn_summary.rejection_rate:.3f}`")
    md_lines.append(f"- High rating ratio (≥4★): `{syn_summary.high_rating_ratio:.3f}`")
    md_lines.append(f"- Low rating ratio (≤2★): `{syn_summary.low_rating_ratio:.3f}`")
    md_lines.append(f"- Rating skew score: `{syn_summary.rating_skew_score:.4f}`")
    md_lines.append(f"- Average sentiment score: `{syn_summary.avg_sentiment_score:.3f}`")
    md_lines.append(f"- Rating histogram: `{json.dumps(syn_summary.rating_histogram)}`")
    md_lines.append("")

    if real_summary is not None:
        md_lines.append("## Real Summary")
        md_lines.append("")
        md_lines.append("### Diversity Metrics")
        md_lines.append(f"- Average vocab diversity: `{real_summary.avg_vocab_diversity:.3f}`")
        md_lines.append(f"- Average semantic novelty: `{real_summary.avg_semantic_novelty:.3f}`")
        md_lines.append(f"- Average domain realism: `{real_summary.avg_domain_realism:.3f}`")
        md_lines.append("")
        md_lines.append("### Quality & Bias Metrics")
        md_lines.append(f"- Rejection rate: `{real_summary.rejection_rate:.3f}`")
        md_lines.append(f"- High rating ratio (≥4★): `{real_summary.high_rating_ratio:.3f}`")
        md_lines.append(f"- Low rating ratio (≤2★): `{real_summary.low_rating_ratio:.3f}`")
        md_lines.append(f"- Rating skew score: `{real_summary.rating_skew_score:.4f}`")
        md_lines.append(f"- Average sentiment score: `{real_summary.avg_sentiment_score:.3f}`")
        md_lines.append(f"- Rating histogram: `{json.dumps(real_summary.rating_histogram)}`")
        md_lines.append("")

        md_lines.append("## Synthetic vs Real (Side-by-side)")
        md_lines.append("")
        md_lines.append("| Metric | Synthetic | Real |")
        md_lines.append("|--------|-----------|------|")
        md_lines.append(
            f"| Average vocab diversity | "
            f"`{syn_summary.avg_vocab_diversity:.3f}` | "
            f"`{real_summary.avg_vocab_diversity:.3f}` |"
        )
        md_lines.append(
            f"| Average semantic novelty | "
            f"`{syn_summary.avg_semantic_novelty:.3f}` | "
            f"`{real_summary.avg_semantic_novelty:.3f}` |"
        )
        md_lines.append(
            f"| Average domain realism | "
            f"`{syn_summary.avg_domain_realism:.3f}` | "
            f"`{real_summary.avg_domain_realism:.3f}` |"
        )
        md_lines.append(
            f"| Rejection rate | `{syn_summary.rejection_rate:.3f}` | "
            f"`{real_summary.rejection_rate:.3f}` |"
        )
        md_lines.append(
            f"| High rating ratio (≥4★) | `{syn_summary.high_rating_ratio:.3f}` | "
            f"`{real_summary.high_rating_ratio:.3f}` |"
        )
        md_lines.append(
            f"| Low rating ratio (≤2★) | `{syn_summary.low_rating_ratio:.3f}` | "
            f"`{real_summary.low_rating_ratio:.3f}` |"
        )
        md_lines.append(
            f"| Avg sentiment score | `{syn_summary.avg_sentiment_score:.3f}` | "
            f"`{real_summary.avg_sentiment_score:.3f}` |"
        )
        md_lines.append("")

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(md_lines), encoding="utf-8")

    typer.echo(f"Quality report written -> {out_path}")


if __name__ == "__main__":
    typer.run(main)
