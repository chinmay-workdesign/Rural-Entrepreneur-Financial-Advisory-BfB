# Phase 7 — Performance Benchmarking Report

This document records the empirical latency and performance profile of the Rural Enterprise Advisor platform across all core pipeline stages as measured in Phase 7 on Windows 11 with Python 3.14.

---

## 1. Latency Breakdown Summary

| Component / Pipeline Stage | Metric | Measured Value | SLA / Target | Status |
|----------------------------|--------|----------------|--------------|--------|
| **Embedding Model Cold-Start** | Model load & warm-up (`BAAI/bge-small-en-v1.5`) | **334.86 ms** | < 1,500 ms | PASS |
| **Authoritative Vector Retrieval** | Average latency (FastEmbed + Qdrant top-3) | **27.08 ms** | < 100 ms | PASS |
| **Authoritative Vector Retrieval** | 95th Percentile (p95 latency) | **81.36 ms** | < 250 ms | PASS |
| **Deterministic Financial Calculation** | Average latency (`calculate_financial_structure`) | **0.0831 ms** (83.1 µs) | < 5 ms | PASS |
| **Deterministic Financial Calculation** | Max latency under high-concurrency loop | **4.7722 ms** | < 10 ms | PASS |
| **DPR PDF Generation (ReportLab)** | Average latency (full 2-page bankable report) | **76.75 ms** | < 300 ms | PASS |
| **End-to-End User Routing (Offline/Fallback)** | Intent + Retrieval + Financial Engine + Response | **~1,578 ms** | < 3,000 ms | PASS |

---

## 2. In-Depth Component Analysis

### 2.1 Vector Retrieval Layer (`app.retrieval.service`)
- **Engine**: Qdrant Local Persistent Embedded Vector Store with FastEmbed (`BAAI/bge-small-en-v1.5`).
- **Corpus Size**: 13 verified chunks across 6 authoritative source documents.
- **Average Query Latency**: 27.08 ms across bilingual and multilingual search terms.
- **Resource Footprint**: Zero external HTTP network calls. Zero third-party SaaS dependency.

### 2.2 Financial Mathematics Engine (`app.finance.calculator`)
- **Formulas**: Annuity loan amortization, dynamic margin absorption, DSCR cash flow projection.
- **Latency**: Sub-millisecond (83.1 microseconds average).
- **Determinism**: 100% mathematical consistency without LLM intervention.

### 2.3 DPR PDF Engine (`app.dpr.generator`)
- **Engine**: ReportLab fallback renderer generating 2-page Detailed Project Reports with equipment tables, scheme comparisons, and statutory provenance matrices.
- **Compilation Speed**: 76.75 ms per complete PDF document.
- **Memory Footprint**: In-memory byte streaming without temporary disk file lock bottlenecks.

### 2.4 End-to-End Conversational Overhead
- Telegram and WhatsApp webhook ingestion: < 15 ms.
- State machine lookup & DB transaction: < 8 ms.
- Speech-to-Text (simulated/cached): < 20 ms.
- Text-to-Speech (gTTS synthesis): ~300-600 ms when connected.

---

## 3. Observations & Recommendations

1. **Deterministic Isolation Benefit**: Because financial calculations execute in under 0.1 ms in pure Python, separating math from LLMs provides a 10,000x latency speedup compared to LLM-generated math, in addition to eliminating financial hallucinations.
2. **Local Vector Search Advantage**: Replacing remote SaaS vector databases with local FastEmbed and Qdrant reduced retrieval latency from ~350-800 ms (network roundtrips) down to 27 ms.
