### OpenAI (gpt-4.1-mini) – Synthetic Quality Summary

On a batch of 200 synthetic reviews generated via the OpenAI `gpt-4.1-mini` model, the guardrail pipeline produced the following metrics:

- **Average vocabulary diversity:** `0.841`  
  The model shows slightly higher lexical variety than the local model, consistently producing fluent and well-phrased reviews with limited repetition.

- **Average semantic novelty:** `0.638`  
  There is a good level of semantic variation across the 200 reviews, although some recurring templates and patterns naturally appear as the dataset grows.

- **Average domain realism:** `0.254`  
  While the reviews are generally coherent, they reference dev-tools concepts in a more generic way compared to Qwen3-30B. Our conservative domain-realism heuristic reflects this by assigning a lower score.

- **Rejection rate:** `0.010` (≈ 1%)  
  A small subset of reviews was automatically rejected by the guardrail rules (e.g., off-domain, too short, or overly generic). In a real pipeline, these samples would be regenerated until they pass all checks.

- **Rating distribution:** `{4: 89, 3: 45, 5: 54, 2: 9, 1: 3}`  
  The dataset maintains a realistic spread of ratings: mostly positive (4–5★), a sizeable portion of mixed/neutral feedback (3★), and a small tail of negative reviews (1–2★), which avoids an unrealistically optimistic synthetic dataset.
