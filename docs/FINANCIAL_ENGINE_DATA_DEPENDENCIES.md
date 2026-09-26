# Financial Engine Data Dependencies & Input Audit

This document maps all financial inputs, parameters, and constants used across `app/finance/calculator.py`, `app/finance/benchmarks.py`, `app/finance/multi_schemes.py`, and `app/finance/repository.py`.

## 1. Input Classification Taxonomy

Every input to the financial engine belongs to one of the following categories:
- **USER_PROVIDED**: Provided by the applicant/entrepreneur (e.g. proposed trade, preferred location, requested project cost).
- **GOVERNMENT_OFFICIAL_BENCHMARK**: Directly sourced from official publications (NABARD Unit Cost Booklet, KVIC/MDTC Model Project Profiles).
- **GOVERNMENT_SCHEME_RULE**: Directly sourced from statutory guidelines or scheme gazettes (e.g. PMEGP Revised Guidelines 2023).
- **DERIVED_MATHEMATICAL**: Deterministically calculated by Python code (reducing-balance EMI, debt service, DSCR).
- **APPLICATION_ASSUMPTION**: Platform-level modeling choices (e.g. conservative default tenures, 5-year cashflow revenue multipliers).
- **SYNTHETIC_BASELINE**: Legacy mock parameters retained solely for baseline tests; disabled when `REAL_DATA_ONLY=True`.

---

## 2. Comprehensive Parameter Dependency Map

| Parameter Name | Module & Symbol | Current Source | Sourcing Category | Authoritative Status | Derived From | Migration Status |
|---|---|---|---|---|---|---|
| **Proposed Project Cost** | `calculator.py` (`project_cost`) | User conversation or benchmark fallback | USER_PROVIDED / BENCHMARK | Context-dependent | N/A | **Migrated**: benchmark reference now sourced from `repository.py` |
| **Minimum Project Cost** | `calculator.py` (`MIN_PROJECT_COST = 5000.0`) | Hardcoded threshold | APPLICATION_ASSUMPTION | Internal standard | N/A | Retained as platform guardrail |
| **MFS Scheme Ceiling** | `calculator.py` (`MFS_CEILING = 140000.0`) | Hardcoded SCA rule | APPLICATION_ASSUMPTION / SCA Norm | Unverified baseline | N/A | Retained as SCA baseline; labelled as policy norm |
| **MFS Max Loan** | `calculator.py` (`MFS_MAX_LOAN = 125000.0`) | Hardcoded SCA rule | APPLICATION_ASSUMPTION / SCA Norm | Unverified baseline | N/A | Retained as SCA baseline |
| **TLS Max Cost Ceiling** | `calculator.py` (`TLS_MAX_COST = 5000000.0`) | Hardcoded SCA rule | APPLICATION_ASSUMPTION / SCA Norm | Unverified baseline | N/A | Retained as SCA baseline |
| **TLS Max Loan** | `calculator.py` (`TLS_MAX_LOAN = 4500000.0`) | Hardcoded SCA rule | APPLICATION_ASSUMPTION / SCA Norm | Unverified baseline | N/A | Retained as SCA baseline |
| **MFS Interest Rate** | `calculator.py` (`rate = 0.065` / 6.5%) | Hardcoded SCA rule | APPLICATION_ASSUMPTION / SCA Norm | Unverified baseline | N/A | Retained as SCA baseline |
| **TLS Interest Rate** | `calculator.py` (`rate = 0.080` / 8.0%) | Hardcoded SCA rule | APPLICATION_ASSUMPTION / SCA Norm | Unverified baseline | N/A | Retained as SCA baseline |
| **MFS Tenure & Moratorium** | `calculator.py` (`tenure_mos=36`, `morat_mos=3`) | Hardcoded SCA rule | APPLICATION_ASSUMPTION / SCA Norm | Unverified baseline | N/A | Retained as SCA baseline |
| **TLS Tenure & Moratorium** | `calculator.py` (`tenure_mos=84`, `morat_mos=6`) | Hardcoded SCA rule | APPLICATION_ASSUMPTION / SCA Norm | Unverified baseline | N/A | Retained as SCA baseline |
| **Loan Amount (SCA)** | `calculator.py` (`loan = min(0.90 * cost, max_loan)`) | Formula calculation | DERIVED_MATHEMATICAL | Deterministic Engine | `project_cost`, `max_loan` | Verified deterministic logic |
| **Beneficiary Margin (SCA)** | `calculator.py` (`margin = cost - loan`) | Formula calculation | DERIVED_MATHEMATICAL | Deterministic Engine | `project_cost`, `loan` | Verified deterministic logic |
| **Equated Monthly Installment (EMI)** | `calculator.py` (`emi = ...`) | Reducing balance formula | DERIVED_MATHEMATICAL | Deterministic Engine | `loan`, `rate`, `repay_mos` | Verified deterministic logic |
| **Dairy Benchmark Cost (2 HF Cows)** | `repository.py` (`_get_dairy_benchmark`) | `data/processed/nabard/karnataka_benchmarks.json` | GOVERNMENT_OFFICIAL_BENCHMARK | `VERIFIED` | NABARD KA UC Booklet 26-27 (p. 41) | **MIGRATED TO REAL DATA** |
| **Poultry Benchmark Cost (2000 Integration)** | `repository.py` (`_get_poultry_benchmark`) | `data/processed/nabard/karnataka_benchmarks.json` | GOVERNMENT_OFFICIAL_BENCHMARK | `VERIFIED` | NABARD KA UC Booklet 26-27 (p. 50) | **MIGRATED TO REAL DATA** |
| **Flour Mill Benchmark Cost** | `repository.py` (`_get_flour_mill_benchmark`) | `data/processed/non_farm/flour_mill_benchmark.json` | GOVERNMENT_OFFICIAL_BENCHMARK | `VERIFIED` (Historical 2020) | Project SAMADHAN Profile (p. 5) | **MIGRATED TO REAL DATA** |
| **Tailoring Benchmark Cost** | `benchmarks.py` (`NABARD_BENCHMARKS[2]`) | In-memory synthetic dict | SYNTHETIC_BASELINE | `DATA_NOT_AVAILABLE` under REAL_DATA_ONLY | None | **FLAGGED**: Real source unavailable; blocked in REAL_DATA_ONLY |
| **Kirana Benchmark Cost** | `benchmarks.py` (`NABARD_BENCHMARKS[0]`) | In-memory synthetic dict | SYNTHETIC_BASELINE | `DATA_NOT_AVAILABLE` under REAL_DATA_ONLY | None | **FLAGGED**: Real source unavailable; blocked in REAL_DATA_ONLY |
| **PMEGP Max Mfg Ceiling** | `multi_schemes.py` | `data/processed/schemes/pmegp_rules.json` | GOVERNMENT_SCHEME_RULE | `VERIFIED` | MoMSME Guidelines (p. 5, Para 3.1) | **MIGRATED TO REAL DATA** (₹50 Lakhs) |
| **PMEGP Max Service Ceiling** | `multi_schemes.py` | `data/processed/schemes/pmegp_rules.json` | GOVERNMENT_SCHEME_RULE | `VERIFIED` | MoMSME Guidelines (p. 5, Para 3.1) | **MIGRATED TO REAL DATA** (₹20 Lakhs) |
| **PMEGP Rural Special Subsidy** | `multi_schemes.py` (`rural_subsidy_pct = 35`) | `data/processed/schemes/pmegp_rules.json` | GOVERNMENT_SCHEME_RULE | `VERIFIED` | MoMSME Guidelines (p. 4, Para 3.2) | **MIGRATED TO REAL DATA** (35%) |
| **PMEGP Rural General Subsidy** | `multi_schemes.py` (`general_subsidy_pct = 25`) | `data/processed/schemes/pmegp_rules.json` | GOVERNMENT_SCHEME_RULE | `VERIFIED` | MoMSME Guidelines (p. 4, Para 3.2) | **MIGRATED TO REAL DATA** (25%) |
| **PMEGP Special Own Contribution** | `multi_schemes.py` (`0.05` / 5%) | `data/processed/schemes/pmegp_rules.json` | GOVERNMENT_SCHEME_RULE | `VERIFIED` | MoMSME Guidelines (p. 4, Para 3.2) | **MIGRATED TO REAL DATA** (5%) |
| **PMEGP Bank Loan Proportion** | `multi_schemes.py` (`cost - subsidy - own`) | Formula rule | DERIVED_MATHEMATICAL | Deterministic Engine | `cost`, `subsidy`, `own_contribution` | Verified rule logic |
| **MUDRA Shishu / Kishore / Tarun Tiers** | `multi_schemes.py` (₹50k / ₹5L / ₹10L) | Hardcoded banking convention | APPLICATION_ASSUMPTION | `NEEDS_SOURCE_VERIFICATION` | Circular not yet in repository | **LABELLED**: Marked unverified pending official end-borrower circular |
| **5-Year Cash Flow Multipliers** | `dpr/generator.py` (`specs = [...]`) | Hardcoded revenue/opex curves | APPLICATION_ASSUMPTION | Standard Financial Modeling | `project_cost`, `emi` | Preserved deterministic projection |
| **Base DSCR Threshold** | `dpr/generator.py` / `dscr.py` (`1.25` / `1.75`) | Banking prudence norm | APPLICATION_ASSUMPTION | Prudence benchmark | `ebitda`, `debt_service` | Preserved deterministic ratio |

---

## 3. Key Findings

1. **Calculated outputs are never government-supplied**: EMI, DSCR, margin amounts, and 5-year projections are derived by deterministic software routines; they do not appear as static constants in official publications.
2. **NABARDSLUCC benchmarks are statutory references**: They represent normative unit costs for the state of Karnataka, not statutory caps on what an entrepreneur may spend.
3. **Model project profiles are historical engineering estimates**: Samadhan Flour Mill (2020) must always carry its publication year to prevent misrepresentation as current market quotations.
4. **Tailoring and Kirana have zero verified source data**: They must explicitly yield `DATA_NOT_AVAILABLE` under `REAL_DATA_ONLY=True`.
