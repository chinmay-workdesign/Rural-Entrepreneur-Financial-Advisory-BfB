# Phase 5 Manual Test Matrix: Local Authoritative RAG & Financial Routing

This document details the manual and programmatic verification of the 8 mandatory test cases defined in Phase 5.
All tests were executed against the runtime engine (`execute_authoritative_routing`) and the Telegram/WhatsApp turn handler (`_handle_user_turn`).

---

## Summary Matrix

| Test ID | User Query | Intent Classified | Engine Used | Authoritative Source Cited | Deterministic Math Verified | Result Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TEST 1** | *"What is the NABARD cost for a 2 cow dairy unit?"* | `FACTUAL` | Local FastEmbed + Qdrant | NABARD Karnataka RO Booklet (p. 41) | N/A (Pure Factual) | **PASS** |
| **TEST 2** | *"How much does a mini flour mill cost?"* | `FACTUAL` | Local FastEmbed + Qdrant | Project SAMADHAN Profile (p. 5) | N/A (Historical 2020 Warning Verified) | **PASS** |
| **TEST 3** | *"What subsidy does PMEGP provide?"* | `FACTUAL` | Local FastEmbed + Qdrant | MoMSME PMEGP Guidelines (p. 4) | N/A (35% rural special, 25% general) | **PASS** |
| **TEST 4** | *"What does AIDIS say about rural indebtedness?"* | `FACTUAL` | Local FastEmbed + Qdrant | NSS 77th Round Report No. 588 (p. 92, 94) | N/A (Contextual Macro Only) | **PASS** |
| **TEST 5** | *"What is the official cost of a kirana shop?"* | `DATA_UNAVAILABLE` | Applicability Guard | None (`DATA_NOT_AVAILABLE`) | None (No Synthetic Fallback) | **PASS** |
| **TEST 6** | *"I want a dairy farm. Calculate EMI for ₹2 lakh."* | `FINANCIAL` | Deterministic Python Engine | None (Pure Math) | EMI: ₹3,564.06, Margin: ₹20,000 | **PASS** |
| **TEST 7** | *"NABARD says dairy costs ₹2.29 lakh. I want to borrow ₹2 lakh. Calculate EMI."* | `MIXED` | Local RAG + Python Engine | NABARD Karnataka RO Booklet (p. 41) | EMI: ₹3,564.06, Loan: ₹1,80,000 | **PASS** |
| **TEST 8** | *"What is the PMMY interest rate?"* | `DATA_UNAVAILABLE` | Verification Status Guard | None (`AUTHORITATIVE_DATA_NOT_AVAILABLE`) | None (No Unsupported Claims) | **PASS** |

---

## Detailed Test Scenarios

### TEST 1: Dairy Factual Inquiry
- **User Query:** *"What is the NABARD cost for a 2 cow dairy unit?"*
- **Intent:** `FACTUAL`
- **Retrieval Output:**
  - Chunk ID: `NABARD_KA_DAIRY_2COW_HF_P41`
  - Source: NABARD Karnataka Regional Office Unit Cost Booklet 2026-27, Page 41
  - Content: 2 Crossbred Cows (HF) total unit cost ₹2,29,000 (Livestock ₹1,70,000, Shed ₹32,500, Insurance ₹10,200).
- **Citation Generated:** `[NABARD Karnataka Unit Cost Booklet 2026, p.41]`
- **Verification Status:** `VERIFIED_OFFICIAL`
- **Output Behavior:** LLM synthesizes explanatory text with citation; no financial arithmetic is generated.

### TEST 2: Flour Mill Historical Warning
- **User Query:** *"How much does a mini flour mill cost?"*
- **Intent:** `FACTUAL`
- **Retrieval Output:**
  - Chunk ID: `SAMADHAN_FLOUR_MILL_COST_P5`
  - Source: Project SAMADHAN / MDTC Flour Mill Model Profile, Page 5
  - Publication Year: 2020
  - Cost Nature: `HISTORICAL_BENCHMARK_2020`
- **Historical Notice Enforced:**
  - Explicit warning attached: *"⚠️ [Note: Stated machinery costs reflect the 2020 Project SAMADHAN model project profile benchmark. Current market costs require up-to-date vendor quotations.]"*
- **Output Behavior:** ₹32.93 Lakhs is presented strictly as a 2020 benchmark without silent inflation adjustment.

### TEST 3: PMEGP Scheme Subsidy Inquiry
- **User Query:** *"What subsidy does PMEGP provide?"*
- **Intent:** `FACTUAL`
- **Retrieval Output:**
  - Chunk ID: `PMEGP_MARGIN_MONEY_SUBSIDY_MATRIX_P4`
  - Source: Ministry of MSME PMEGP Revised Guidelines 2022-23, Page 4
- **Citation Generated:** `[PMEGP Revised Guidelines 2022-23, p.4]`
- **Output Content:** 35% Margin Money subsidy in rural areas for special category (SC/ST/OBC/Women/Ex-servicemen), 25% for general category; 5% vs 10% own equity.

### TEST 4: AIDIS Rural Indebtedness Macro Statistics
- **User Query:** *"What does AIDIS say about rural indebtedness?"*
- **Intent:** `FACTUAL`
- **Retrieval Output:**
  - Chunk ID: `AIDIS_KA_RURAL_IOI_DEBT_P92_94`
  - Source: National Statistical Office (NSO) NSS 77th Round Report No. 588, Pages 92, 94
- **Citation Generated:** `[AIDIS NSS Report No. 588, p.92]`
- **Output Content:** 48.1% Incidence of Indebtedness in rural Karnataka; 67.2% institutional credit share, 32.5% non-institutional share.
- **Isolation Check:** Macro survey statistics are strictly excluded from borrower credit evaluation.

### TEST 5: Kirana Shop Official Cost (Unavailable Benchmark)
- **User Query:** *"What is the official cost of a kirana shop?"*
- **Intent:** `DATA_UNAVAILABLE`
- **Guard Enforced:** Semantic similarity override protection prevents returning Dairy or Poultry chunks.
- **Output Behavior:**
  - Returns clear explanation: *"⚠️ Official Benchmark Not Available (DATA_NOT_AVAILABLE): The official NABARD Karnataka Unit Cost Booklet does not contain prescribed benchmark costs for Kirana. Evaluation for this activity is customized strictly to your submitted project quotation. No synthetic or unverified benchmarks are substituted."*
- **Synthetic Fallback Prevention:** Confirmed zero synthetic dictionary leakage when `REAL_DATA_ONLY=True`.

### TEST 6: Pure Financial Inquiry
- **User Query:** *"I want a dairy farm. Calculate EMI for ₹2 lakh."*
- **Intent:** `FINANCIAL`
- **Engine Executed:** Deterministic Python Financial Engine (`calculate_financial_structure(200000.0)`).
- **Values Computed (Immutable):**
  - Project Cost: ₹2,00,000.00
  - Concessional Bank Loan: ₹1,80,000.00 (90%)
  - Beneficiary Margin: ₹20,000.00 (10%)
  - Monthly Installment (EMI): ₹3,564.06 (at 7.0% p.a. reducing balance over 60 months)
- **Retrieval Check:** `retrieval_used: False`. LLM does not generate or alter the math.

### TEST 7: Mixed Benchmark and Calculation Inquiry
- **User Query:** *"NABARD says dairy costs ₹2.29 lakh. I want to borrow ₹2 lakh. Calculate EMI."*
- **Intent:** `MIXED`
- **Combined Execution:**
  - **Factual Component:** Retrieves NABARD Karnataka Booklet Page 41 (`[NABARD Karnataka Unit Cost Booklet 2026, p.41]`).
  - **Financial Component:** Python engine calculates EMI for ₹2,00,000 project outlay (EMI: ₹3,564.06).
- **Prompt Structure:** System prompt injects both the immutable deterministic calculation and the retrieved evidence chunk.
- **Result:** Response presents verified NABARD benchmark alongside the exact Python-calculated EMI.

### TEST 8: PMMY Unverified End-Borrower Rules Inquiry
- **User Query:** *"What is the PMMY interest rate?"*
- **Intent:** `DATA_UNAVAILABLE`
- **Verification Status Check:**
  - `PMMY_PARTNER_ELIGIBILITY` is tagged as `NEEDS_SOURCE_VERIFICATION` for end-borrower rules.
- **Output Behavior:**
  - System declines to present unverified partner refinance rules as end-borrower statutory rules.
  - Explains that official borrower-level interest rates remain unverified in the indexed repository.
