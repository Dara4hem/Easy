from pathlib import Path
import json

import typer

from .config import load_config
from .generation import generate_many_stub, generate_many_openai


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
        help="Which generator to use: 'stub' or 'openai'.",
    ),
    model_name: str = typer.Option(
        "gpt-4.1-mini",
        help="Model name for LLM providers (e.g. gpt-4.1-mini, gpt-4o-mini).",
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

    if provider == "stub":
        typer.echo("Using stub generator (no LLM).")
        reviews = generate_many_stub(cfg, num_reviews)
    elif provider == "openai":
        typer.echo(f"Using OpenAI provider with model={model_name}")
        reviews = generate_many_openai(cfg, num_reviews, model=model_name)
    else:
        typer.echo(f"Unknown provider '{provider}'. Use 'stub' or 'openai'.")
        raise typer.Exit(code=1)

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for r in reviews:
            f.write(json.dumps(r.model_dump(mode="json"), ensure_ascii=False) + "\n")

    typer.echo(f"Generated {len(reviews)} reviews → {out_path}")


if __name__ == "__main__":
    typer.run(main)
