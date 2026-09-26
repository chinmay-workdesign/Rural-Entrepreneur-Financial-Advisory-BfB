# Deep Repository Audit: Rural Enterprise Advisor (Synthetic Baseline vs. Real Data Migration)

**Document Version:** 1.0.0  
**Audit Date:** 2026-09-25  
**Auditor:** Antigravity AI  
**Repository Branch:** `real-data-migration` (Derived from `synthetic-baseline`)  

---

## 1. Current Architecture

Inspection of the physical repository demonstrates the actual software architecture in production:

```
[ User (Telegram / WhatsApp) ]
              │
              ▼
[ Ingestion & Routing (FastAPI / Webhook / Polling) ]
       │                                  │
       ▼                                  ▼
[ app/telegram/webhook_handler.py ]   [ app/whatsapp/webhook_handler.py ]
       │                                  │
       └──────────────────┬───────────────┘
                          │
                          ▼
            [ app/dialogue/conversation_state.py ]
         (Session State Machine: GREETING, COLLECTING,
             CONFIRM_DPR, SUBMITTED, LANGUAGE_SELECTION)
              │                     ▲
              │                     │
              ├─────────────────────┼──────────────────────────────┐
              ▼                     ▼                              ▼
      [ Voice Pipeline ]     [ Entity Extraction ]       [ In-Memory Benchmarks ]
   app/voice/voice_service.py app/ai/extraction.py     app/finance/benchmarks.py
    (Gemini STT + gTTS)     (Gemini JSON prompt +     (8 Hardcoded Trade Records)
                             Regex Fallback)                       │
                                    │                              │
                                    ▼                              ▼
                          [ Financial Engine ] <───────────────────┘
                       app/finance/calculator.py
                       app/finance/dscr.py
                       app/finance/multi_schemes.py
                                    │
                                    ▼
                         [ Advisory Generation ]
                          app/ai/extraction.py
                        (Gemini 2.5 Flash / Template)
                                    │
                                    ▼
                         [ DPR PDF Generator ]
                         app/dpr/generator.py
                       (ReportLab fallback engine)
                                    │
                                    ▼
                          [ Persistence Layer ]
                           app/db/models.py
                           (SQLite / PostgreSQL)
```

### Contrast with Architectural Claims (README.md)
* **Vector DB / Qdrant:** The README documents a Qdrant Cloud collection (`nabard_benchmarks`) queried via semantic cosine similarity. **Reality:** Qdrant is **NOT** present in `requirements.txt` or anywhere in the codebase. Benchmarks are loaded from a hardcoded Python list in `app/finance/benchmarks.py`.
* **Agent Orchestration (JEV):** The README references an agent orchestration layer. **Reality:** No agent framework (JEV, LangGraph, AutoGen) exists in the repository. Orchestration is a procedural state machine in `conversation_state.py`.
* **Speech-to-Text:** Handled directly via Google Gemini multimodal audio in `app/ai/gemini_client.py` and TTS via `gTTS`.

---

## 2. Synthetic Data Inventory

| Synthetic Data | File | Function/Class | Current Usage | Replacement Source | Classification | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **8 Trade Capex/Opex/DSCR** | `app/finance/benchmarks.py` | `NABARD_BENCHMARKS` | Baseline investment sizing and default viability score | NABARD State Unit Cost Booklets (e.g. Karnataka DPD) | **BENCHMARK** | P0 |
| **Conservative Default Benchmark** | `app/finance/benchmarks.py` | `get_trade_benchmark()` | Fallback if user trade keyword is not matched | Statistical median from ASUSE / NSSO | **BENCHMARK** | P1 |
| **MFS Ceiling & Loan Cap** | `app/finance/calculator.py` | `MFS_CEILING`, `MFS_MAX_LOAN` | Divides MFS vs TLS; caps loan at ₹1.25L | State SCA / NBCFDC scheme guidelines | **POLICY** | P0 |
| **TLS Cost & Loan Cap** | `app/finance/calculator.py` | `TLS_MAX_COST`, `TLS_MAX_LOAN` | Upper ceiling on Term Loan Scheme (₹50L / ₹45L) | State SCA / NBCFDC scheme guidelines | **POLICY** | P0 |
| **MFS/TLS Interest Rates** | `app/finance/calculator.py` | `calculate_financial_structure` | Static 6.5% (MFS) and 8.0% (TLS) | Official SCA lending schedules | **POLICY** | P0 |
| **Tenure & Moratoriums** | `app/finance/calculator.py` | `calculate_financial_structure` | 36m (3m morat) & 84m (6m morat) | Official SCA lending circulars | **POLICY** | P0 |
| **MUDRA Scheme Tiers** | `app/finance/multi_schemes.py` | `get_all_eligible_schemes` | Static limits: ₹50k, ₹5L, ₹10L; rates 8.5%-11.5% | PMMY / DFS official directives | **POLICY** | P0 |
| **PMEGP Subsidy Percentages** | `app/finance/multi_schemes.py` | `get_all_eligible_schemes` | 35% rural special, 25% rural general, 5% own margin | KVIC PMEGP 2023 Guidelines | **POLICY** | P0 |
| **Sectoral Scheme Rules** | `app/finance/multi_schemes.py` | `get_sector_specific_scheme` | Fixed limits & rates for KCC (₹2L @ 4%), PVCF, Vishwakarma | RBI PSL Master Directions & Ministry Guidelines | **POLICY** | P1 |
| **Asset Turnover Multiplier** | `app/finance/dscr.py` | `project_financial_cashflows` | Estimates annual revenue as `cost * 1.80` | ASUSE GVA/turnover survey empirical ratios | **ASSUMPTION** | P1 |
| **Opex Ratio** | `app/finance/dscr.py` | `project_financial_cashflows` | Estimates annual expenses as `revenue * 0.65` | ASUSE / NABARD model trade operating budgets | **ASSUMPTION** | P1 |
| **5-Year Growth Ratios** | `app/dpr/generator.py` | `_get_5year_cashflows` | Multipliers (1.6x - 2.5x turnover) across 5 years | NABARD bankable model project profiles | **ASSUMPTION** | P1 |
| **Equipment Allocation Pcts** | `app/dpr/generator.py` | `_get_trade_equipment_items` | Arbitrary percentage breakdown of capex & working capital | NABARD model scheme asset itemization | **BENCHMARK** | P1 |
| **Default Family Income** | `app/dialogue/conversation_state.py` | `_handle_dpr_generation` | Defaults family income to ₹65,000 if null | AIDIS rural household income/asset percentiles | **STATISTICAL** | P2 |
| **Default Demo Accounts** | `app/db/crud.py` | `seed_default_users` | Hardcoded demo accounts for authentication | Environment/RBAC directory | **TEST FIXTURE** | P3 |

---

## 3. Hardcoded Financial Rules

Every single financial parameter in the application is currently a static constant embedded in Python code:

1. **`app/finance/calculator.py`**:
   * Minimum Project Cost: `5000.0`
   * MFS Cost Ceiling: `140000.0`
   * MFS Loan Cap: `125000.0`
   * MFS Interest Rate: `0.065` (6.5% p.a.)
   * MFS Tenure: `36` months (3 months moratorium, 33 repayment months)
   * TLS Cost Ceiling: `5000000.0`
   * TLS Loan Cap: `4500000.0`
   * TLS Interest Rate: `0.080` (8.0% p.a.)
   * TLS Tenure: `84` months (6 months moratorium, 78 repayment months)
   * Primary Loan Proportion: `0.90` (90% of outlay)
2. **`app/finance/multi_schemes.py`**:
   * MUDRA Shishu: $\le$ `50000.0` (100% loan, 0% margin, `8.5% - 9.5%` interest)
   * MUDRA Kishore: $\le$ `500000.0` (85% loan, 15% margin, `9.5% - 10.5%` interest)
   * MUDRA Tarun: $\le$ `1000000.0` (85% loan capped at ₹10L, `10.0% - 11.5%` interest)
   * PMEGP Subsidy: `35%` (Special Rural), `25%` (General Rural), Beneficiary Contribution: `5%` (Special), `10%` (General)
   * KCC Livestock: `min(cost * 0.90, 200000.0)` at `4.0%` effective interest
   * PVCF Poultry: `cost * 0.75` loan, `cost * 0.25` capital subsidy, interest `8.0% - 10.0%`
   * PM Vishwakarma: `cost * 0.95` capped at ₹1L (Phase 1) or ₹2L (Phase 2), `5.0%` fixed interest
   * PM SVANidhi: `min(cost, 50000.0)`, `0%` margin, `7.0%` interest subsidy
   * PM-FME: `cost * 0.65` loan, `35%` capital subsidy capped at ₹10,00,000, `10%` margin
3. **`app/finance/dscr.py`**:
   * Baseline DSCR Threshold for Bankability: `dscr >= 1.25`
   * Default Turnover Multiplier: `project_cost * 1.80`
   * Default Opex Ratio: `annual_revenue * 0.65`

---

## 4. Current Data Flow

```text
User Message (Text or Spoken Audio)
  │
  ▼
app/dialogue/conversation_state.py
  │
  ├─► [Voice Service] (app/voice/voice_service.py)
  │   transcribe_audio() via Gemini Multimodal STT
  │
  ├─► [Language Detection] (conversation_state.py)
  │   detect_message_language() via Unicode frequency & keywords
  │
  ├─► [Entity Extraction] (app/ai/extraction.py)
  │   extract_entrepreneur_details() via Gemini JSON schema (or fallback_regex_extractor)
  │   Returns: trade, district, state, available_capital, project_cost
  │
  ├─► [Completeness Gate] (conversation_state.py)
  │   If trade, district, or project_cost is missing: halts calculation and returns clarification question.
  │
  ├─► [Deterministic Financial Engine] (app/finance/calculator.py)
  │   validate_project_cost() -> calculate_financial_structure()
  │   Produces: scheme, cost, loan, margin, rate, emi, total_interest
  │
  ├─► [In-Memory Benchmark Query] (app/finance/benchmarks.py)
  │   get_trade_benchmark(trade, district)
  │   Matches keyword in 8 hardcoded dicts -> Returns capex, opex, DSCR
  │
  ├─► [Cash Flow Projection] (app/finance/dscr.py)
  │   project_financial_cashflows() -> Projects annual cash flows & bankable status
  │
  ├─► [Multi-Scheme Optimization] (app/finance/multi_schemes.py)
  │   get_all_eligible_schemes() -> Compiles SCA, MUDRA, PMEGP, Sectoral options
  │
  ├─► [Advisory Formulation] (app/ai/extraction.py)
  │   generate_advisory_message() -> Passes locked numbers into Gemini prompt
  │   (Falls back to regional template if Gemini fails or script check fails)
  │
  ├─► [Outbound Message Dispatch] (app/telegram/client.py or app/whatsapp/client.py)
  │   Sends text/voice advisory to user
  │
  └─► [DPR PDF Compilation] (Triggered when user replies "GENERATE DPR")
      app/dpr/generator.py -> generate_dpr_pdf() via ReportLab
      app/storage/local_storage.py -> saves PDF to static/dprs/
      Dispatches PDF document directly to Telegram/WhatsApp channel
```

---

## 5. Current RAG Architecture

* **Vector Database:** `NONE` (Zero vector database code exists; Qdrant is absent from dependencies and source files).
* **Embedding Model:** `NONE`.
* **Payload Structure:** `NONE`.
* **Knowledge Retrieval:** Pure keyword substring search over 8 dictionary objects in `app/finance/benchmarks.py`.
* **Delivery to LLM:** A single synthetic summary string (`"Grounded in NABARD <trade> benchmark: typical capex ₹X, opex ₹Y."`) is passed into `{nabard_benchmark}` in the Gemini system prompt.

---

## 6. Current Financial Engine

1. **Inputs:** `project_cost: float` (sanitized and validated).
2. **Validation:** Checks `5000.0 <= project_cost <= 5000000.0`.
3. **Scheme Selection:**
   $$\text{scheme} = \begin{cases} \text{MICRO\_FINANCE}, & \text{if } \text{cost} \le 1,40,000 \\ \text{TERM\_LOAN}, & \text{if } \text{cost} > 1,40,000 \end{cases}$$
4. **Loan & Margin:**
   $$\text{loan} = \min(0.90 \times \text{cost}, \text{max\_loan})$$
   $$\text{margin} = \text{cost} - \text{loan}$$
   $$\text{loan} + \text{margin} \equiv \text{cost}$$
5. **EMI Formula:** Standard reducing-balance annuity formula:
   $$\text{EMI} = \frac{\text{loan} \times r \times (1 + r)^n}{(1 + r)^n - 1}$$
   where $r = \frac{\text{annual\_rate}}{12}$, $n = \text{tenure} - \text{moratorium}$.
6. **DSCR Formula:**
   $$\text{DSCR} = \frac{\text{Net Annual Operating Income}}{\text{Annual Debt Service}}$$

---

## 7. Current Tests

* **Test Suite:** Located in `tests/` (32 tests across 8 files).
* **Baseline Run Results (2026-09-25):** **30 Passed, 2 Failed**.
* **Failures Analysis:**
  * `test_dialogue_state.py::test_full_dialogue_to_sanction_flow` failed due to `AssertionError: assert None == 'Belagavi'`.
  * `test_telegram_channel.py::test_telegram_end_to_end_dialogue_to_sanction` failed due to `AssertionError: assert 'COLLECTING' == 'CONFIRM_DPR'`.
  * **Root Cause of Baseline Failures:** When live Google Gemini API keys are invalid or deprecated (logs show `403 PERMISSION_DENIED` and `404 NOT_FOUND: models/gemini-2.5-flash is no longer available`), the system falls back to `fallback_regex_extractor`. The regex extractor extracted the cost but missed the district in complex sentences, leaving the state in `COLLECTING`.
* **Tests Bound to Synthetic Numbers:**
  * `test_finance_calculator.py`: Strictly asserts `loan == 108000.0`, `rate == 6.5`, `loan == 450000.0`, `rate == 8.0`.
  * `test_dialogue_state.py`: Asserts `fin["rate"] == 6.5`, `fin["repayment_months"] == 33`.
  * `test_telegram_channel.py`: Asserts `fin["loan"] == 252000.0`, `fin["rate"] == 8.0`.

---

## 8. Migration Risk Map

1. **Calculator Decoupling Risk:** `app/finance/calculator.py` has embedded constants. Removing these constants and substituting external policy rules must not alter the mathematical invariance $\text{loan} + \text{margin} = \text{cost}$.
2. **Offline Resilience Risk:** Live Gemini API calls frequently fail or suffer network timeouts. The fallback extraction must be enhanced so real data lookups do not crash during offline operation.
3. **District / State Specificity Risk:** The existing code assumes Karnataka SCA parameters regardless of user location. Introducing real state-specific schemes requires the engine to gracefully handle missing state data.
4. **DPR Template Formatting Risk:** The ReportLab PDF generator in `app/dpr/generator.py` has rigid table column widths. Injecting longer official scheme names or extensive citations could cause page overflow unless dynamically formatted.
