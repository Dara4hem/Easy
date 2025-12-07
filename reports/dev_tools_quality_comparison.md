# Dev Tools Review Quality – Summary

This section is my own comparison between:
- **Synthetic – OpenAI** (`dev_tools_openai_scored.jsonl`, 200 reviews)  
- **Synthetic – Qwen3-30B (Ollama)** (`dev_tools_qwen30b_scored.jsonl`, 300 reviews)  
- **Real – G2 Postman reviews** (`postman_g2_reviews.jsonl`, 50 reviews)

---

## 1. Synthetic Quality – OpenAI vs Qwen3-30B

Both synthetic sets are scored with the same `annotate_quality` pipeline.

**OpenAI (200 reviews)**  
- Avg vocab diversity: **0.84**  
- Avg semantic novelty: **0.64**  
- Avg domain realism: **0.25**  
- Rejection rate: **1%**  
- Rating histogram: `{5: 54, 4: 89, 3: 45, 2: 9, 1: 3}`  
- Behavior: very clean language, slightly more “generic SaaS review” tone.

**Qwen3-30B (300 reviews)**  
- Avg vocab diversity: **0.80**  
- Avg semantic novelty: **0.62**  
- Avg domain realism: **0.40**  
- Rejection rate: **1.7%**  
- Rating histogram: `{5: 104, 4: 117, 3: 68, 2: 10, 1: 1}`  
- Behavior: more tool-specific and realistic (collections, environments, CI, auth, etc.), slightly noisier language but closer to real dev usage.

**My take:**  
- I will treat **OpenAI** as the “high-polish / generic” source.  
- I will treat **Qwen3-30B** as the “high-realism / dev-focused” source and give it more weight.

---

## 2. Real G2 Postman Reviews

For grounding, I collected **50 real Postman reviews from G2**:

- Avg rating: **4.65 / 5**  
- Rating range: **4.0 – 5.0** (very positive slice)  
- Avg length: **≈ 205 words**  



