# Scheme Rule Lineage & Statutory Verification Audit

This document records the exact lineage, source documents, and verification standing of all scheme-related parameters used in the multi-scheme structuring engine (`app/finance/multi_schemes.py`) and financial calculator (`app/finance/calculator.py`).

## 1. Scheme Parameter Verification Summary

| Scheme | Rule / Constant | Current Value in Engine | Authoritative Source Document | Source Page & Section | Verification Status | Operational Handling in Engine |
|---|---|---|---|---|---|---|
| **PMEGP** | Max Project Cost (Manufacturing) | ₹50,00,000.00 | Ministry of MSME Revised Guidelines 2022-23 (`PMEGP_REVISED_GUIDELINES_2023`) | Page 5, Para 3.1 | `VERIFIED_OFFICIAL` | Directly grounded in `data/processed/schemes/pmegp_rules.json` |
| **PMEGP** | Max Project Cost (Business/Service) | ₹20,00,000.00 | Ministry of MSME Revised Guidelines 2022-23 (`PMEGP_REVISED_GUIDELINES_2023`) | Page 5, Para 3.1 | `VERIFIED_OFFICIAL` | Directly grounded in `data/processed/schemes/pmegp_rules.json` |
| **PMEGP** | Margin Money Subsidy (Rural Special) | 35.0% of project cost | Ministry of MSME Revised Guidelines 2022-23 (`PMEGP_REVISED_GUIDELINES_2023`) | Page 4, Para 3.2(i) Table | `VERIFIED_OFFICIAL` | Sourced from `pmegp_rules.json` (SC/ST/OBC/Women/Minority/Ex-servicemen/PH) |
| **PMEGP** | Margin Money Subsidy (Rural General) | 25.0% of project cost | Ministry of MSME Revised Guidelines 2022-23 (`PMEGP_REVISED_GUIDELINES_2023`) | Page 4, Para 3.2(i) Table | `VERIFIED_OFFICIAL` | Sourced from `pmegp_rules.json` |
| **PMEGP** | Margin Money Subsidy (Urban Special) | 25.0% of project cost | Ministry of MSME Revised Guidelines 2022-23 (`PMEGP_REVISED_GUIDELINES_2023`) | Page 4, Para 3.2(i) Table | `VERIFIED_OFFICIAL` | Sourced from `pmegp_rules.json` |
| **PMEGP** | Margin Money Subsidy (Urban General) | 15.0% of project cost | Ministry of MSME Revised Guidelines 2022-23 (`PMEGP_REVISED_GUIDELINES_2023`) | Page 4, Para 3.2(i) Table | `VERIFIED_OFFICIAL` | Sourced from `pmegp_rules.json` |
| **PMEGP** | Own Equity Contribution (Special) | 5.0% of project cost | Ministry of MSME Revised Guidelines 2022-23 (`PMEGP_REVISED_GUIDELINES_2023`) | Page 4, Para 3.2(i) Table | `VERIFIED_OFFICIAL` | Sourced from `pmegp_rules.json` |
| **PMEGP** | Own Equity Contribution (General) | 10.0% of project cost | Ministry of MSME Revised Guidelines 2022-23 (`PMEGP_REVISED_GUIDELINES_2023`) | Page 4, Para 3.2(i) Table | `VERIFIED_OFFICIAL` | Sourced from `pmegp_rules.json` |
| **PMEGP** | Minimum Age Requirement | 18 Years | Ministry of MSME Revised Guidelines 2022-23 (`PMEGP_REVISED_GUIDELINES_2023`) | Page 5, Para 4.1(i) | `VERIFIED_OFFICIAL` | Sourced from `pmegp_rules.json` |
| **PMEGP** | Minimum Educational Qualification | VIII Standard Pass (for > ₹10L Mfg, > ₹5L Service) | Ministry of MSME Revised Guidelines 2022-23 (`PMEGP_REVISED_GUIDELINES_2023`) | Page 6, Para 4.1(ii) | `VERIFIED_OFFICIAL` | Sourced from `pmegp_rules.json` |
| **PMEGP** | Mandatory Registration | Udyam Portal | Ministry of MSME Revised Guidelines 2022-23 (`PMEGP_REVISED_GUIDELINES_2023`) | Page 7, Para 4.1(viii) | `VERIFIED_OFFICIAL` | Sourced from `pmegp_rules.json` |
| **PMEGP** | Repayment Tenure Range | 3 to 7 Years | Ministry of MSME Revised Guidelines 2022-23 (`PMEGP_REVISED_GUIDELINES_2023`) | Page 10, Para 8 | `VERIFIED_OFFICIAL` | Sourced from `pmegp_rules.json` |
| **PMMY / MUDRA** | Max Refinance Loan Ceiling | ₹20,00,000.00 | MUDRA Partner Eligibility (`PMMY_PARTNER_ELIGIBILITY`) | Page 1, Para 2.1 | `NEEDS_SOURCE_VERIFICATION` | Refinance term for banks, not end-borrower rule |
| **PMMY / MUDRA** | Borrower Tiers (Shishu, Kishore, Tarun) | Up to ₹50k / ₹5L / ₹10L | Institutional Portal Material (Ministry of Finance / MUDRA) | Circular pending in repo | `NEEDS_SOURCE_VERIFICATION` | Retained as illustrative option; explicitly marked `NEEDS_SOURCE_VERIFICATION`; never promoted to verified |
| **SCA MFS** | Micro Finance Scheme Ceiling | ₹1,40,000.00 | NBCFDC / SCA Operational Norms | Unverified in current repo | `APPLICATION_ASSUMPTION` / Baseline Policy | Explicitly labelled as State Channelizing Agency policy baseline; not claimed as Union Govt gazette |
| **SCA MFS** | Maximum Loan | ₹1,25,000.00 (90%) | NBCFDC / SCA Operational Norms | Unverified in current repo | `APPLICATION_ASSUMPTION` / Baseline Policy | Retained as deterministic SCA baseline |
| **SCA MFS** | Concessional Interest Rate | 6.50% p.a. | NBCFDC / SCA Operational Norms | Unverified in current repo | `APPLICATION_ASSUMPTION` / Baseline Policy | Retained as deterministic SCA baseline |
| **SCA TLS** | Term Loan Scheme Max Ceiling | ₹50,00,000.00 | NMDFC / SCA Operational Norms | Unverified in current repo | `APPLICATION_ASSUMPTION` / Baseline Policy | Retained as deterministic SCA baseline |
| **SCA TLS** | Concessional Interest Rate | 8.00% p.a. | NMDFC / SCA Operational Norms | Unverified in current repo | `APPLICATION_ASSUMPTION` / Baseline Policy | Retained as deterministic SCA baseline |

---

## 2. Rules for Real-Data Migration Compliance

1. **PMEGP**: All calculations in `multi_schemes.py` reference the exact parameters from `data/processed/schemes/pmegp_rules.json`.
2. **PMMY**: Because end-borrower guidelines are marked `NEEDS_SOURCE_VERIFICATION`, the engine flags PMMY recommendations with `verification_status: "NEEDS_SOURCE_VERIFICATION"` and includes an explicit note that borrower guidelines are awaiting an official gazette circular.
3. **SCA (MFS & TLS)**: The engine labels these schemes as `source_type: "APPLICATION_POLICY_BASELINE"` rather than attributing them to an unverified gazette.
