### Qwen3-30B (Ollama) – Synthetic Quality Summary

On a batch of 300 synthetic reviews generated locally via Qwen3-30B (Unsloth GGUF on Ollama), the guardrail pipeline produced the following metrics:

- **Average vocabulary diversity:** `0.799`  
  The model uses reasonably varied language across reviews, avoiding excessive repetition of the same phrases.

- **Average semantic novelty:** `0.619`  
  As the dataset scales to 300 samples, semantic overlap naturally increases, but there is still a healthy amount of variation in how users, scenarios, and pain points are described.

- **Average domain realism:** `0.396`  
  Reviews frequently mention domain-specific concepts such as API debugging, CI/CD pipelines, environment variables, and sprint workflows. The score is intentionally conservative due to strict keyword-based heuristics.

- **Rejection rate:** `0.017` (≈ 1.7%)  
  A small fraction of reviews were automatically rejected as low quality (e.g., too short, off-domain, or repetitive) by the guardrail rules. In a production pipeline, these samples would be regenerated until they pass the checks.

- **Rating distribution:** `{4: 117, 5: 104, 3: 68, 2: 10, 1: 1}`  
  The synthetic dataset exhibits a realistic rating distribution where most reviews are positive (4–5★), a meaningful portion are neutral/mixed (3★), and a small tail of negative feedback (1–2★) still exists.
