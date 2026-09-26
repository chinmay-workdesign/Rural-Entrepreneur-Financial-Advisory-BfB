# Local FastEmbed + Qdrant Authoritative Retrieval Evaluation Report

This document records the empirical evaluation of the **Local Authoritative Knowledge Retrieval** layer using a 16-query ground truth test suite across physical government and NABARD documents.

---

## 1. Evaluation Methodology & Benchmark Classification

> [!NOTE]
> **Benchmark Classification: B. Internal Regression Benchmark**
> This evaluation suite is an internal regression and consistency test suite designed to verify that dense embeddings correctly map authoritative domain queries to expected source documents, page numbers, and verification statuses without index degradation. It is **NOT** an independent open-domain IR benchmark across large distractor corpora. Accordingly, results reflect **100% on the internal 16-query regression set**.

- **Corpus**: 6 physical source documents in `data/raw/` (13 structured chunks).
- **Index**: Local persistent Qdrant collection `authoritative_knowledge` at `data/qdrant_db/` indexed with cosine distance.
- **Embedding Model**: FastEmbed ONNX quantized `BAAI/bge-small-en-v1.5` (384 dimensions).
- **Evaluation Dataset**: 16 manually verified ground truth queries covering livestock unit costs, equipment schedules, scheme subsidy matrices, survey statistics, and unverified partner guidelines.
- **Metric Definitions**:
  - **Precision@1**: Percentage of queries where the top-1 retrieved chunk matches the expected source authority.
  - **Precision@3**: Percentage of queries where the expected source authority appears within the top 3 retrieved chunks.
  - **Recall@5**: Percentage of queries where the expected source authority is retrieved within top 5 candidates.
  - **Page Correctness (Top-3)**: Percentage of queries where the exact source page is retrieved within top 3 candidates.
  - **Status Correctness (Top-1)**: Percentage of queries where top-1 result accurately preserves official vs unverified standing.

---

## 2. Benchmark Summary Metrics

| Metric | Result | Count / Total | Target Threshold | Assessment |
|---|---|---|---|---|
| **Precision@1** | **100.0%** | 16 / 16 | ≥ 85.0% | **EXCELLENT** |
| **Precision@3** | **100.0%** | 16 / 16 | ≥ 90.0% | **EXCELLENT** |
| **Recall@5** | **100.0%** | 16 / 16 | ≥ 95.0% | **EXCELLENT** |
| **Page Correctness (Top-3)** | **100.0%** | 16 / 16 | ≥ 85.0% | **EXCELLENT** |
| **Status Correctness (Top-1)** | **100.0%** | 16 / 16 | 100.0% | **EXCELLENT** |
| **Average Retrieval Latency** | **14.50 ms** | 16 queries | < 50.0 ms | **ZERO-LATENCY** |
| **Max Retrieval Latency** | **65.51 ms** | Cold-start / PMMY | < 150.0 ms | **PASS** |
| **Min Retrieval Latency** | **8.74 ms** | In-memory cache | — | **FAST** |

---

## 3. Query-by-Query Evaluation Breakdown

| Query ID | User Query | Expected Source & Page | Top-1 Retrieved Source | Top-1 Page | Relevance Score | Latency | Status Match |
|---|---|---|---|---|---|---|---|
| **Q1** | 2 cow dairy unit cost in Karnataka | NABARD (p. 41) | `NABARD_KA_UC_BOOKLET_2026_27` | 41 | 0.830 | 21.1 ms | `PASS` (`VERIFIED_OFFICIAL`) |
| **Q2** | Jersey cow model unit cost | NABARD (p. 41) | `NABARD_KA_UC_BOOKLET_2026_27` | 41 | 0.819 | 9.6 ms | `PASS` (`VERIFIED_OFFICIAL`) |
| **Q3** | cost of cattle shed for 2 crossbred cows | NABARD (p. 41) | `NABARD_KA_UC_BOOKLET_2026_27` | 41 | 0.823 | 11.4 ms | `PASS` (`VERIFIED_OFFICIAL`) |
| **Q4** | 2000 broiler poultry integration unit cost | NABARD (p. 50) | `NABARD_KA_UC_BOOKLET_2026_27` | 50 | 0.838 | 10.0 ms | `PASS` (`VERIFIED_OFFICIAL`) |
| **Q5** | commercial 5000 broiler poultry farm project cost | NABARD (p. 49) | `NABARD_KA_UC_BOOKLET_2026_27` | 49 | 0.833 | 14.1 ms | `PASS` (`VERIFIED_OFFICIAL`) |
| **Q6** | mini flour mill total project cost 2020 | SAMADHAN (p. 5) | `SAMADHAN_FLOUR_MILL_PROJECT_PROFILE` | 5 | 0.817 | 8.7 ms | `PASS` (`VERIFIED_OFFICIAL`) |
| **Q7** | flour mill plant and machinery equipment cost | SAMADHAN (p. 6) | `SAMADHAN_FLOUR_MILL_PROJECT_PROFILE` | 6 | 0.815 | 9.5 ms | `PASS` (`VERIFIED_OFFICIAL`) |
| **Q8** | flour mill manpower requirement and employee salaries | SAMADHAN (p. 4) | `SAMADHAN_FLOUR_MILL_PROJECT_PROFILE` | 4 | 0.875 | 9.7 ms | `PASS` (`VERIFIED_OFFICIAL`) |
| **Q9** | PMEGP rural special category margin money subsidy | MoMSME (p. 4) | `PMEGP_REVISED_GUIDELINES_2023` | 4 | 0.844 | 9.6 ms | `PASS` (`VERIFIED_OFFICIAL`) |
| **Q10** | PMEGP manufacturing maximum project cost ceiling | MoMSME (p. 4) | `PMEGP_REVISED_GUIDELINES_2023` | 4 | 0.753 | 11.1 ms | `PASS` (`VERIFIED_OFFICIAL`) |
| **Q11** | PMEGP minimum age and education qualification criteria | MoMSME (p. 5) | `PMEGP_REVISED_GUIDELINES_2023` | 5 | 0.846 | 11.2 ms | `PASS` (`VERIFIED_OFFICIAL`) |
| **Q12** | PMEGP loan repayment tenure years | MoMSME (p. 5) | `PMEGP_REVISED_GUIDELINES_2023` | 5 | 0.770 | 8.9 ms | `PASS` (`VERIFIED_OFFICIAL`) |
| **Q13** | rural incidence of indebtedness in Karnataka AIDIS | NSS Report 588 (p. 92) | `AIDIS_NSS_77_REPORT_588` | 92 | 0.896 | 11.7 ms | `PASS` (`VERIFIED_OFFICIAL`) |
| **Q14** | informal non-institutional moneylender interest rates in rural Karnataka | NSS Report 588 (p. 97) | `AIDIS_NSS_77_REPORT_588` | 97 | 0.875 | 10.0 ms | `PASS` (`VERIFIED_OFFICIAL`) |
| **Q15** | RBI priority sector lending targets for agriculture and micro enterprises | RBI PSL (p. 10) | `RBI_PSL_MASTER_DIRECTIONS_2025` | 10 | 0.831 | 9.9 ms | `PASS` (`VERIFIED_OFFICIAL`) |
| **Q16** | PMMY MUDRA refinance eligibility for partner banks | PMMY (p. 1) | `PMMY_PARTNER_ELIGIBILITY` | 1 | 0.883 | 65.5 ms | `PASS` (`NEEDS_SOURCE_VERIFICATION`) |

---

## 4. Operational Invariant Verification

1. **Unverified Source Demotion**:
   When queried with `require_verified=True`, `PMMY_PARTNER_ELIGIBILITY` is excluded with 0 false-positive leakage into verified advisory.
2. **Table Semantic Preservation**:
   All 16 queries returned formatted line-item descriptions and monetary amounts rather than fragmented number sequences.
3. **Execution Latency**:
   End-to-end vector embedding generation + cosine nearest neighbor search completes in an average of **14.50 ms**, making it completely suitable for interactive conversational bots without noticeable latency.
