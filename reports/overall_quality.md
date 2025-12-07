## Synthetic Model Comparison (OpenAI vs Qwen3-30B)

> Note: metrics computed on a small pilot sample (3 reviews per model). Final numbers will be reported on the full 300–500 sample dataset.

| Metric                 | OpenAI (gpt-4.1-mini) | Qwen3-30B (Ollama) |
|------------------------|------------------------|---------------------|
| Avg vocab diversity    | `0.831`                | `0.800`             |
| Avg semantic novelty   | `0.797`                | `0.827`             |
| Avg domain realism     | `0.317`                | `0.350`             |
| Rejection rate         | `0.000`                | `0.000`             |
| Rating histogram       | `{3: 2, 5: 1}`         | `{4: 2, 3: 1}`      |

**High-level takeaways**

- OpenAI produces **slightly richer vocabulary**, but its reviews are a bit less novel and slightly less “on-domain”.
- Qwen3-30B, running fully locally via Ollama, generates **more diverse and slightly more domain-focused** reviews.
- Both models pass the current guardrails (0% rejection) – thresholds can be tightened later to enforce stricter quality.
