from pathlib import Path
import json

import typer

from .config import load_config
from .generation import (
    generate_many_stub,
    generate_many_openai,
    generate_many_ollama,
)


def main(
    config: str = typer.Option(
        "configs/dev_tools.yaml",
        help="Path to YAML config file.",
    ),
    num_reviews: int = typer.Option(
        10,
        help="Number of synthetic reviews to generate.",
    ),
    output: str = typer.Option(
        "data/synthetic/dev_tools_stub.jsonl",
        help="Path to output JSONL file.",
    ),
    provider: str = typer.Option(
        "stub",
        help="Which generator to use: 'stub', 'openai', or 'ollama'.",
    ),
    model_name: str = typer.Option(
        "gpt-4.1-mini",
        help="Model name for LLM providers (e.g. gpt-4.1-mini, gpt-4o-mini, or an Ollama model name).",
    ),
    use_guardrails: bool = typer.Option(
        False,
        "--guardrails",
        help="Enable automatic rejection/regeneration for low-quality samples.",
    ),
):
    """
    Read config and generate synthetic reviews using stub or an LLM provider.
    """
    cfg_path = Path(config)
    if not cfg_path.exists():
        typer.echo(f"Config file not found: {cfg_path}")
        raise typer.Exit(code=1)

    cfg = load_config(cfg_path)
    typer.echo(f"Loaded config for domain: {cfg.domain}")

    if use_guardrails:
        typer.echo(f"Using {provider} provider with model={model_name} (with guardrails)")
        from .generation import generate_many_with_guardrails
        reviews, elapsed, total_attempts = generate_many_with_guardrails(
            cfg, num_reviews, provider, model_name
        )
        avg_time = elapsed / len(reviews) if reviews else 0.0
        rejection_rate = 1.0 - (len(reviews) / total_attempts) if total_attempts else 0.0
        typer.echo(f"Generation time: {elapsed:.2f}s total, {avg_time:.3f}s per review")
        typer.echo(f"Total attempts: {total_attempts}, accepted: {len(reviews)}, rejection rate: {rejection_rate:.1%}")
    else:
        if provider == "stub":
            typer.echo("Using stub generator (no LLM).")
            reviews, elapsed = generate_many_stub(cfg, num_reviews)
        elif provider == "openai":
            typer.echo(f"Using OpenAI provider with model={model_name}")
            reviews, elapsed = generate_many_openai(cfg, num_reviews, model=model_name)
        elif provider == "ollama":
            typer.echo(f"Using Ollama provider with model={model_name}")
            reviews, elapsed = generate_many_ollama(cfg, num_reviews, model=model_name)
        else:
            typer.echo(f"Unknown provider '{provider}'. Use 'stub', 'openai', or 'ollama'.")
            raise typer.Exit(code=1)
        
        # Report timing
        avg_time = elapsed / len(reviews) if reviews else 0.0
        typer.echo(f"Generation time: {elapsed:.2f}s total, {avg_time:.3f}s per review")

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for r in reviews:
            f.write(json.dumps(r.model_dump(mode="json"), ensure_ascii=False) + "\n")

    typer.echo(f"Generated {len(reviews)} reviews -> {out_path}")


if __name__ == "__main__":
    typer.run(main)
