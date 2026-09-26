# JEV & Retrieval Architecture: Authoritative Knowledge Retrieval

> [!WARNING]
> **SUPERSEDED IN PHASE 5**: JEV / Typesafe AI integration was deprecated and eliminated due to paused API signups.
> The production retrieval architecture is 100% local, zero-cost FastEmbed + Qdrant. See [LOCAL_RAG_ARCHITECTURE.md](file:///c:/Users/sabar/Desktop/Proj/Rural%20Advisory/docs/LOCAL_RAG_ARCHITECTURE.md).

This document defines the historical architectural boundaries, dependency audit, and operational contract for the **Authoritative Knowledge Retrieval** layer in the **Rural Enterprise Advisor** system.

---

## 1. Audit of Existing Repository Dependencies & Claims

Prior to Phase 4, the repository status was as follows:

| Component | Repository Claim / Mention | Actual State Prior to Phase 4 | Phase 4 Architecture |
|---|---|---|---|
| **Vector DB (Qdrant)** | Mentioned in early README drafts (`nabard_benchmarks` collection via cosine similarity) | Not instantiated; no collection files or client calls existed in code | **Local Persistent Qdrant**: `QdrantClient(path="data/qdrant_db")` using 384-dim cosine distance collections for authoritative knowledge. |
| **Embedding Engine** | Claimed FastEmbed / BAAI embeddings in planning notes | `fastembed` library present in virtualenv, model cached locally | **Local FastEmbed (`BAAI/bge-small-en-v1.5`)**: 384-dimensional dense vectors generated offline with zero external cloud dependencies. |
| **Agent / JEV Layer** | Referenced as an orchestration layer | Procedural state machine in `conversation_state.py`; no JEV/LangGraph framework | **Grounded Evidence Retrieval**: Independent Python service providing verified document chunks with cryptographic provenance to the dialogue LLM. |
| **Financial Engine Boundary** | Financial calculations performed deterministically | Implemented in `calculator.py` and `dscr.py` with 51 passing tests | **Strict Boundary**: Vector retrieval is strictly prohibited from performing arithmetic, EMI calculations, DSCR ratios, or loan sizing. |

---

## 2. Invariant Boundary: Retrieval vs. Financial Engine

```
                      USER QUERY
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
 [Retrieval Pipeline]            [Deterministic Engine]
  - Semantic Search (Qdrant)      - Parameter Extraction
  - Filter by Verification        - Equity & Concessional Loan Math
  - Grounded Chunks               - Reducing-Balance EMI & DSCR
          │                               │
          ▼                               ▼
  Retrieved Evidence            Deterministic Result
  (Sources, Pages, Quotes)      (Exact INR Amounts & Tiers)
          │                               │
          └───────────────┬───────────────┘
                          ▼
            [Grounded Advisory LLM]
             - Cites Sources & Pages
             - Explains Financial Structure
             - Alerts on Historical Baseline
             - Flags Gaps (Tailoring/Kirana)
```

### Non-Negotiable Architectural Rules:
1. **Never Calculate in RAG**: The vector database and LLM must never compute EMIs, subsidies, margins, or DSCRs. All math executes through `calculate_financial_structure` and `calculate_dscr`.
2. **Never Fabricate Missing Data**: If an activity (e.g. Tailoring, Kirana) lacks an authoritative source, retrieval yields no verified chunks, and the repository returns `DATA_NOT_AVAILABLE`.
3. **Preserve Source Trust Hierarchy**:
   - `VERIFIED_OFFICIAL`: NABARD, PMEGP Guidelines, AIDIS NSS Report 588, Project SAMADHAN Model Profile.
   - `NEEDS_SOURCE_VERIFICATION`: PMMY partner refinance guidelines (end-borrower rules unverified).
   - Unverified chunks must never be masqueraded as official gazette rules.
4. **Historical Profiling Warning**: Retrieval of SAMADHAN Flour Mill data preserves `publication_year: 2020` and `cost_nature: "HISTORICAL_BENCHMARK_2020"`.
