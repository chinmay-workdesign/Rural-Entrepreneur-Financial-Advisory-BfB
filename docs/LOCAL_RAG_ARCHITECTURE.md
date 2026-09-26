# Local Authoritative RAG Architecture (Zero-Cost, Fully Local)

## 1. Why JEV / Typesafe AI is Not Used
External paid RAG SaaS and third-party hosted indexing services (such as JEV / Typesafe AI, Pinecone, or OpenAI vector stores) are **strictly eliminated** from this project:
1. **Zero External Signup / API Dependency:** New Typesafe AI / JEV signups are paused. Relying on an unavailable or gated API halts open-source reproducibility.
2. **Cost Neutrality & Sovereignty:** Rural micro-enterprise advisory requires zero-cost, locally executable deployment without recurring per-query SaaS fees.
3. **Deterministic Local Grounding:** Authoritative government circulars (NABARD, MoMSME, RBI, NSO) must be cryptographically hashed and verified locally on disk.

The retrieval stack is **FastEmbed (`BAAI/bge-small-en-v1.5`)** and **Qdrant (Local Embedded on disk or Docker Compose)**.

---

## 2. Core Architecture & Separation of Concerns

```
                     ┌───────────────────────────────┐
                     │     Authoritative Sources     │
                     │  (PDFs in data/raw/ + SHA256) │
                     └───────────────┬───────────────┘
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │   Structured Table Ingestion  │
                     │  (Preserves Units, Pages, Hdr)│
                     └───────────────┬───────────────┘
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │      Local FastEmbed ONNX     │
                     │    (BAAI/bge-small-en-v1.5)   │
                     └───────────────┬───────────────┘
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │   Local Qdrant Collection     │
                     │   (data/qdrant_db/ or Docker) │
                     └───────────────┬───────────────┘
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │   Evidence Retrieval Service  │
                     │  (require_verified=True, hash)│
                     └───────────────┬───────────────┘
                                     │
              ┌──────────────────────┴──────────────────────┐
              ▼                                             ▼
    ┌────────────────────────┐                   ┌────────────────────────┐
    │     FACTUAL PATH       │                   │    FINANCIAL PATH      │
    │  (Authoritative Query) │                   │   (Loan / EMI Outlay)  │
    └───────────┬────────────┘                   └──────────┬─────────────┘
                │                                           │
                ▼                                           ▼
    ┌────────────────────────┐                   ┌────────────────────────┐
    │    RetrievedEvidence   │                   │  Deterministic Python  │
    │ (Page, Source, Status) │                   │  (EMI, DSCR, Margin)   │
    └───────────┬────────────┘                   └──────────┬─────────────┘
                │                                           │
                └─────────────────────┬─────────────────────┘
                                      ▼
                        ┌───────────────────────────┐
                        │   Grounded Context Builder│
                        │   (Math Immutability Rules│
                        │   + Dynamic Citations)    │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │       Gemini / LLM        │
                        │ (Narrative synthesis only)│
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │   Telegram / WhatsApp     │
                        │   (Text + Voice Output)   │
                        └───────────────────────────┘
```

---

## 3. FastEmbed Dense Embedding Configuration
- **Model:** `BAAI/bge-small-en-v1.5` (quantized ONNX runtime execution on CPU).
- **Vector Dimension:** 384 dimensions.
- **Distance Metric:** Cosine Similarity (`Distance.COSINE`).
- **Normalization:** L2-normalized dense embeddings computed without external network calls.
- **Speed:** ~11 ms average per query embedding on standard CPU.

---

## 4. Qdrant Local Deployment Modes
The system supports two local operational modes configured via `app/config.py`:
1. **Mode A — Embedded On-Disk (Default & Tested):**
   - Config: `settings.QDRANT_URL = None`
   - Filesystem Location: `data/qdrant_db/`
   - Zero background services or Docker daemons needed; fully compatible with Windows, macOS, and Linux CI environments.
2. **Mode B — Containerized Local Qdrant (Docker Compose):**
   - Config: `settings.QDRANT_URL = "http://localhost:6333"`
   - Started via `docker compose up -d qdrant`
   - Ports: `6333` (REST/Web UI), `6334` (gRPC).

---

## 5. Ingestion Pipeline & Table-Preserving Chunking
Standard sliding-window text chunking destroys tabular semantics in financial PDFs. The ingestion pipeline (`app/retrieval/ingest.py`) implements structured semantic chunking:
1. **Table Context Preservation:** Explicit column and row labels are retained alongside itemized costs (e.g. Livestock, Civil Shed, Insurance, Concentrate Feed).
2. **Provenance Attachment:** Each chunk contains the original document's SHA-256 hash, official title, authoring organization, publication year, verification status, and PDF page number.
3. **Backup Export:** Chunks are mirrored to `data/processed/retrieval_chunks.json`.

---

## 6. Verification Status & Source Trust Filtering
Every indexed point contains `verification_status`:
- `VERIFIED_OFFICIAL`: Official government/NABARD source verified against raw PDF on disk.
- `NEEDS_SOURCE_VERIFICATION`: E.g., PMMY partner refinance guidelines (unverified for borrower rules).
- `DATA_NOT_AVAILABLE`: E.g., Kirana and Tailoring unit costs.

Default retrieval enforces `require_verified=True`. Unverified documents are strictly excluded from borrower-facing advice.

---

## 7. Semantic Similarity Override Protection
Vector embeddings measure cosine distance, which can cause high similarity between unrelated trade questions (e.g., asking for a "Kirana shop unit cost" might pull "Dairy cow unit cost").
- **Guard:** Under `REAL_DATA_ONLY=True`, queries for known unavailable trades (`kirana`, `tailoring`) bypass vector search and immediately return `DATA_NOT_AVAILABLE`.

---

## 8. Flour Mill Historical 2020 Notice
Project SAMADHAN Flour Mill Profile was published in **2020** (₹32.93 Lakhs total project cost).
- Whenever retrieved, the router and prompt builder attach a mandatory historical warning:
  `⚠️ [Note: Stated machinery costs reflect the 2020 Project SAMADHAN model project profile benchmark. Current market costs require up-to-date vendor quotations.]`
- The system never inflates, deflates, or fabricates current market numbers.

---

## 9. Multilingual & Voice Integration
- **Languages:** English, Hindi, Kannada, Telugu, Marathi.
- **Principle:** The retrieval index remains in authoritative English. The LLM translates and explains the evidence in the applicant's language while preserving numbers, percentages, and citations intact.
- **Voice Flow:** Voice note -> STT transcription -> Normalized text -> Intent router -> RAG / Financial engine -> LLM -> TTS synthesis -> Voice reply.

---

## 10. Observability & Logging
Every query execution logs structured JSON with:
`request_id`, `intent`, `retrieval_used`, `retrieval_count`, `source_ids`, `source_pages`, `verification_status`, `financial_engine_used`, `llm_used`, `response_language`, `retrieval_latency_ms`, `financial_latency_ms`, `llm_latency_ms`, `total_latency_ms`.
