# Phase 8 Baseline & Environment Freeze Report

**Date / Timestamp:** 2026-09-26T10:18:00+05:30  
**Branch:** `real-data-migration`  
**Git Commit Hash:** `3f1d08649f59e5cd86cd23a15c7d840558090f68`

---

## 1. System & Environment Specification

| Component | Specification / Version |
|---|---|
| **Operating System** | Windows 11 Enterprise (10.0.26200-SP0) |
| **Python Runtime** | Python 3.14.7 (tags/v3.14.7:823f032, Aug 5 2026, 10:51:32) [MSC v.1944 64 bit (AMD64)] |
| **pytest** | 9.1.1 |
| **FastAPI** | 0.141.1 |
| **Qdrant Client** | 1.19.0 |
| **FastEmbed** | 0.8.0 |
| **ReportLab** | 5.0.1 |
| **Embedding Engine** | `BAAI/bge-small-en-v1.5` (Local ONNX Runtime CPU) |
| **Vector Store** | Local Embedded Qdrant on disk (`data/qdrant_db/`) & Docker Compose support |
| **Financial Engine** | Deterministic Python 3.14 (`app/finance/calculator.py`) |

---

## 2. Baseline Test Results

### 2.1 Pytest Test Suite
```
Total Tests:    138
Passed:         138 (100%)
Failed:         0
Skipped:        0
Warnings:       6 (FastAPI / Starlette testclient deprecations; Python 3.14 typing warnings)
Execution Time: 419.06 seconds
```

Breakdown:
- **Baseline Unit / Integration Tests:** 88 / 88 Passed
- **Phase 7 End-to-End Test Suite (`tests/e2e/`):** 50 / 50 Passed
  - `test_real_world_flows.py`: 12 / 12 Passed
  - `test_llm_financial_integrity.py`: 9 / 9 Passed
  - `test_dpr_real_data_provenance.py`: 3 / 3 Passed
  - `test_channels_and_voice.py`: 13 / 13 Passed
  - `test_failure_injection.py`: 10 / 10 Passed
  - `test_data_lineage_traceability.py`: 3 / 3 Passed

---

## 3. Authoritative Source Validation Results

Executed via:
```powershell
py scripts/validate_sources.py
py scripts/validate_nabard_data.py
py scripts/validate_aidis_data.py
py scripts/validate_non_farm_data.py
py scripts/validate_policy_data.py
```

| Validation Script | Scope Checked | Result | Status |
|---|---|---|---|
| `validate_sources.py` | 6 raw PDFs in `data/raw/` vs. `sources_manifest.json` | 6 / 6 SHA-256 hashes matched | **PASS** |
| `validate_nabard_data.py` | 12 agricultural & allied records from NABARD UC Booklet 2020-21 | 12 / 12 verified; 3 confirmed `DATA_NOT_AVAILABLE` | **PASS** |
| `validate_aidis_data.py` | 16 rural credit and debt statistics from NSS Report No. 588 | 16 / 16 verified | **PASS** |
| `validate_non_farm_data.py` | 1 non-farm model project profile (Project SAMADHAN Flour Mill 2020) | 1 / 1 verified (₹32.93L, Page 5) | **PASS** |
| `validate_policy_data.py` | 14 PMEGP rules + 3 PMMY partner refinance rules | 17 / 17 verified | **PASS** |

---

## 4. Retrieval Evaluation Benchmark Results

Executed via:
```powershell
py scripts/evaluate_retrieval.py
```

```
Total Queries Evaluated:    23
Precision@1:                100.0% (23/23)
Precision@3:                100.0% (23/23)
Recall@5:                   100.0% (23/23)
Page Correctness (Top-3):   100.0% (23/23)
Status Correctness (Top-1): 100.0% (23/23)
Average Retrieval Latency:  24.62 ms
Min Retrieval Latency:      9.77 ms
Max Retrieval Latency:      269.71 ms
```

---

## 5. Current Verified Data Sources

1. `data/raw/nabard/Karnataka Unit Cost 2020-21.pdf` (SHA-256: `945e4ba8...`)
   - Source ID: `NABARD_KA_UC_BOOKLET_2026_27` (Karnataka RO SLUCC)
   - Verified Activities: 2-Cow Dairy (HF ₹2.29L / Jersey ₹2.05L, p.41), Poultry (Broiler 2000 Integration ₹4.56L, p.50; 5000 Commercial ₹20.80L, p.49), Sheep Rearing (10+1 Bannur ₹1.11L / Local ₹0.98L, p.56), Goat Rearing (10+1 Improved ₹1.13L / Local ₹0.95L, p.60), Piggery (3+1 Fattening ₹1.64L, p.64), Inland Fisheries (1 Ha Pond ₹8.29L, p.68), Beekeeping (10 Colony ₹62.8K, p.30), Sericulture (1 Ha Mulberry ₹2.25L, p.34).
2. `data/raw/schemes/Project samadhan mini flour mill.pdf` (SHA-256: `fa0ca348...`)
   - Source ID: `SAMADHAN_FLOUR_MILL_PROJECT_PROFILE`
   - Verified Activity: Mini Flour Mill (2400 MT/yr capacity, ₹32,93,000 project cost, Page 5, Benchmark Year: 2020).
3. `data/raw/schemes/PMEGP Revised Guidelines.pdf` (SHA-256: `f56ebc68...`)
   - Source ID: `PMEGP_REVISED_GUIDELINES_2023`
   - Verified Scheme Rules: Max project cost ₹50L (mfg) / ₹20L (service), 35% rural special subsidy, 5% own contribution, age ≥ 18, education ≥ VIII pass, Udyam registration mandatory.
4. `data/raw/aidis/NSS Report 588 AIDIS.pdf` (SHA-256: `18e7e1c8...`)
   - Source ID: `AIDIS_NSS_77_REPORT_588`
   - Verified Statistics: All-India rural debt share institutional 66.1% (p.94), All-India IOI 35.0% (p.92), Average Debt per HH ₹59,748 (p.16), Debt-Asset Ratio 3.8% (p.18), Karnataka rural institutional debt share 67.2% (p.94).
5. `data/raw/rbi/RBI Master Directions PSL.pdf` (SHA-256: `5797825b...`)
   - Source ID: `RBI_PSL_MASTER_DIRECTIONS_2025`
   - Verified Norms: 7.5% ANBC target for micro-enterprises, allied agricultural credit eligibility without statutory ceiling.
6. `data/raw/schemes/PMMY MUDRA partner eligibility.pdf` (SHA-256: `56193744...`)
   - Source ID: `PMMY_PARTNER_ELIGIBILITY`
   - Verified Norms: Partner bank refinance ceiling ₹20 Lakhs, max tenure 36 months, target sectors: manufacturing, trading, service.

---

## 6. Current Known Limitations & Boundary Rules

1. **Kirana / Village Grocery:** `DATA_NOT_AVAILABLE` under `REAL_DATA_ONLY=True`. No government unit cost booklet or official model profile exists in the repository.
2. **Tailoring:** `DATA_NOT_AVAILABLE` under `REAL_DATA_ONLY=True`.
3. **PMMY Borrower Rules:** `AUTHORITATIVE_DATA_NOT_AVAILABLE` for borrower interest rates. MUDRA guidelines define institutional refinance rules; borrower interest rates are determined by individual lending banks.
4. **Flour Mill Benchmark Age:** The official Project SAMADHAN profile is from 2020 with a ₹32.93 lakh cost. It must never be presented as a current 2026 spot market quotation, and warning notices are mandatory on conversational outputs and generated DPR PDFs.
5. **No External Paid RAG:** System is strictly committed to local FastEmbed and Qdrant; zero third-party vector/RAG services are permitted.
6. **Financial Arithmetic Isolation:** All loan amounts, margins, subsidies, EMIs, and DSCR values are strictly computed in Python. LLM math is disabled and programmatically overwritten if hallucinated.

---

## 7. Current Deployment Blockers for Production

1. **Environment Configuration Gap (`.env.example`):**
   - Lacks declaration of `QDRANT_URL`, `QDRANT_COLLECTION`, `REAL_DATA_ONLY`, `AUTH_SECRET_KEY`, and clear classification of Required vs. Optional vs. Development vs. Production variables.
2. **Missing Health/Readiness Endpoints:**
   - FastAPI lacks dedicated `/health` and `/readiness` probes reporting application status, local Qdrant collection availability, and configuration integrity without leaking internal secrets.
3. **Structured Logging / Observability Gaps:**
   - Request-level correlation IDs (`X-Correlation-ID`) are not yet systematically threaded across Telegram runner, WhatsApp webhooks, and retrieval pipeline.
4. **Security Hardening Needs:**
   - Insecure development default secret key in `app/config.py` (`AUTH_SECRET_KEY`).
   - Lack of path traversal protection and file size limits on potential file upload endpoints.
   - Webhook replay protection audit and token masking in logs.
5. **Documentation & Runbooks:**
   - Missing dedicated Qdrant operational runbook (`docs/QDRANT_OPERATIONS.md`), deployment guide (`docs/DEPLOYMENT_GUIDE.md`), security audit report (`docs/PHASE8_SECURITY_AUDIT.md`), and comprehensive demo walkthrough (`docs/DEMO_SCRIPT.md`).

---

## 8. File Modification Boundaries for Phase 8

### Files that Need Modification / Addition:
- `.env.example` (Update with complete, classified, secret-free template)
- `app/config.py` (Add production config validation, environment classification, and safe defaults)
- `app/main.py` (Add `/health`, `/readiness`, correlation ID middleware, security headers)
- `docs/QDRANT_OPERATIONS.md` (New runbook for Mode A and Mode B)
- `docs/PHASE8_SECURITY_AUDIT.md` (New comprehensive security audit)
- `docs/PHASE8_DATA_GOVERNANCE.md` (New source governance matrix)
- `docs/PHASE8_OBSERVABILITY.md` (New structured logging and tracing guide)
- `docs/PHASE8_PERFORMANCE.md` (Updated Phase 8 performance profile)
- `docs/DEPLOYMENT_GUIDE.md` (New reproducible clean-machine setup guide)
- `docs/DEMO_SCRIPT.md` (New 10-scenario demo script)
- `docs/PHASE8_PRODUCTIONIZATION_REPORT.md` (Final 20-section deliverable)
- `tests/test_config.py` / `tests/test_health.py` (New tests for config validation and readiness probes)

### Files that MUST NOT be Modified:
- `app/finance/calculator.py` (Deterministic financial engine — FROZEN)
- `data/manifests/sources_manifest.json` (Cryptographic SHA-256 baseline — FROZEN)
- `data/processed/nabard/unit_costs.json` (Verified benchmarks — FROZEN)
- `data/processed/aidis/credit_statistics.json` (Verified AIDIS statistics — FROZEN)
- `data/processed/schemes/pmegp_rules.json` (Verified PMEGP rules — FROZEN)
- `data/raw/*` (Authoritative source PDFs — FROZEN)
- `scripts/validate_*.py` and `scripts/evaluate_retrieval.py` (Authoritative validation rules — FROZEN)
