# kgr-gemma4: Graph-Guided Local Code Agent with Gemma 4

Official repository for the research paper and experimental pipeline submitted to the **Google - The Gemma 4 Developer Agent Paper Track** on Kaggle.

* **Target Models:** `google/gemma-4-E4B-it` (`Gemma 4 - gemma-4 - V1`) & `embeddinggemma-2` (740M)
* **Hardware Target:** Consumer / Single-Accelerator Setup (`GPU T4 x2`)
* **Benchmark:** `princeton-nlp/SWE-bench_Lite` (`split="test"`, `n_issues=40`, `seed=42`)
* **Track Targets:** Best Paper ($15,000), Best New Resource ($10,000), and Best New Application ($10,000)

---

## 1. Overview & Motivation

State-of-the-art software engineering (SWE) agents rely on massive cloud-hosted API models, placing automated code repair out of reach for offline and consumer-hardware workflows. While small local models can run on a single accelerator, they struggle with multi-turn repository navigation, quadratic KV-cache saturation, and the **"Grounded but Wrong"** trade-off (locating the right code region but generating syntactically or structurally invalid patches).

**`kgr-gemma4`** addresses these limitations by combining:
1. **Repository Graph Construction (`ast` -> `networkx`):** Parses Python repositories into `File`, `Class`, `Function`, and `Test` nodes connected by `DEFINES`, `CALLS`, `IMPORTS`, `INHERITS`, and `TESTED_BY` edges.
2. **Deterministic AST Slicing (`DependencyPruner`):** Prunes irrelevant execution branches via `ast.NodeVisitor` before context assembly.
3. **Multi-Channel Hybrid Retrieval:** Fuses lexical `BM25`, AST symbols, dense vectors (`embeddinggemma-2`), and graph neighborhood traversal within a strict budget (`top_k=10` functions, `context_char_budget=24000` characters / ~6k tokens).
4. **Iterative Multi-Turn Reasoning & Verification:** Executes a structured `Strategist` -> `Graph Navigation` -> `Critic` (`critic_rounds=2`) -> `Patch Generation` -> `Graph Verifier` (`verifier_rounds=2`) loop.

---

## 2. Architecture Pipeline

```text
[Issue Description + Repository Codebase (SWE-bench Lite)]
       │
       ▼
[1. Repository Graph Builder (Python ast -> networkx + DependencyPruner)]
  ├── Nodes: File, Class, Function, Test
  └── Edges: DEFINES, CALLS, IMPORTS, INHERITS, TESTED_BY
       │
       ▼
[2. Hybrid Context Retriever]
  ├── Lexical (BM25 + AST Symbols) + Dense (embeddinggemma-2) + Graph Hops
  └── Context Budget: top_k=10 functions, context_char_budget=24000 (~6k tokens)
       │
       ▼
[3. Local Gemma 4 SWE Agent (google/gemma-4-E4B-it)]
  ├── Strategist & Graph Navigation
  ├── Critic Re-planning (critic_rounds=2)
  └── Graph Verifier & Patch Revision (verifier_rounds=2, temperature=0.0)
       │
       ▼
[4. Evaluation & Export]
  ├── 7-Way Ablation Harness (A1-A7): Recall@k, MRR, Groundedness, Type I/II/III Errors
  └── SWE-bench Official Format Export (predictions.jsonl)
