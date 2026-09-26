# Real Data Migration Status & Scope Audit

This document tracks the verified real-data migration status for pilot enterprise activities, government schemes, and financial benchmarks in the **Rural Enterprise Advisor** system.

## 1. Enterprise Activity Benchmark Coverage

| Activity | Real Source | Status | Source Type | Notes |
|---|---|---|---|---|
| **Dairy Farming** (2 Crossbred Cows HF / Jersey) | NABARD Karnataka Unit Cost Booklet 2026-27 (`NABARD_KA_UC_BOOKLET_2026_27`) | `VERIFIED` | `NABARD_UNIT_COST` | HF Cow: ₹2,29,000 (Page 41, Table 1); Jersey Cow: ₹2,05,000. Reconciled breakdown includes livestock, civil shed, insurance, and initial feed/concentrates. |
| **Poultry Broiler Farming** | NABARD Karnataka Unit Cost Booklet 2026-27 (`NABARD_KA_UC_BOOKLET_2026_27`) | `VERIFIED` | `NABARD_UNIT_COST` | Broiler 2000 Birds (Integration): ₹4,56,000 (Page 50, Table 8); Broiler 5000 Birds (Commercial): ₹20,80,000 (Page 49, Table 7). |
| **Sheep Rearing** (10+1 Bannur / Local Breed) | NABARD Karnataka Unit Cost Booklet 2026-27 (`NABARD_KA_UC_BOOKLET_2026_27`) | `VERIFIED` | `NABARD_UNIT_COST` | Bannur 10+1: ₹1,11,000 (Page 56, Table 2); Local 10+1: ₹98,000. Reconciled breakdown includes 1 ram + 10 ewes, shed, grazing, feed, insurance, and shearing. |
| **Goat Rearing** (10+1 Improved / Local Breed) | NABARD Karnataka Unit Cost Booklet 2026-27 (`NABARD_KA_UC_BOOKLET_2026_27`) | `VERIFIED` | `NABARD_UNIT_COST` | Improved 10+1: ₹1,13,000 (Page 60, Table 6); Local 10+1: ₹95,000. Reconciled breakdown includes 1 buck + 10 does, shed, grazing, feed, vet aid, and insurance. |
| **Piggery Farming** (3+1 Fattening Unit) | NABARD Karnataka Unit Cost Booklet 2026-27 (`NABARD_KA_UC_BOOKLET_2026_27`) | `VERIFIED` | `NABARD_UNIT_COST` | 3 Sows + 1 Boar rearing cum fattening unit: ₹1,64,000 (Page 64, Table 8). Reconciled breakdown includes animals, 280 sq.ft sty, 1HP pumpset, and 9-month feed. |
| **Fisheries and Aquaculture** (1 Ha Freshwater Pond) | NABARD Karnataka Unit Cost Booklet 2026-27 (`NABARD_KA_UC_BOOKLET_2026_27`) | `VERIFIED` | `NABARD_UNIT_COST` | 1 ha composite freshwater fish culture: ₹8,29,000 (Page 68, Table 1). Reconciled breakdown includes excavation, fingerlings, and feed inputs. Ornamental: ₹1,50,000. |
| **Beekeeping / Apiary** (10 Colony Unit) | NABARD Karnataka Unit Cost Booklet 2026-27 (`NABARD_KA_UC_BOOKLET_2026_27`) | `VERIFIED` | `NABARD_UNIT_COST` | 10 colony apiary: ₹62,800 (Page 30, Table 6). Includes 10 boxes, 10 colonies, stands, honey extractor, smoker, wax sheets, and 1-year sugar feeding. |
| **Sericulture** (1 Ha Mulberry Garden) | NABARD Karnataka Unit Cost Booklet 2026-27 (`NABARD_KA_UC_BOOKLET_2026_27`) | `VERIFIED` | `NABARD_UNIT_COST` | 1 hectare mulberry garden establishment: ₹2,25,000 (Page 34, Table 1). Irrigated plantation cost with 5-year repayment and 1-year grace period. |
| **Mini Flour Mill (Atta / Maida / Sooji / Chokar)** | Project SAMADHAN / Multi Disciplinary Training Centre Pre-Feasibility Report (`SAMADHAN_FLOUR_MILL_PROJECT_PROFILE`) | `VERIFIED` | `MODEL_PROJECT_PROFILE` | Model project profile (2020) for 2400 MT/year installed capacity. Total Project Cost: ₹32.93 Lakhs (Plant & Machinery ₹23.84L, Working Capital margin ₹5.56L, Furniture ₹0.70L, Preliminary ₹2.38L, Erection ₹0.45L). Employs 12 staff. |
| **Tailoring & Garment Stitching Shop** | None | `DATA_NOT_AVAILABLE` | Future Scope | Absent from NABARD Agriculture Unit Cost booklet. No official KVIC / MSME model project profile ingested yet. Synthetic fallback disabled when `REAL_DATA_ONLY=True`. |
| **Kirana Stall / Village Grocery Store** | None | `DATA_NOT_AVAILABLE` | Future Scope | Absent from NABARD Agriculture Unit Cost booklet. Non-farm retail micro-enterprise requires official PMEGP/MUDRA retail guidelines. Synthetic fallback disabled when `REAL_DATA_ONLY=True`. |

---

## 2. Policy & Scheme Coverage

| Scheme / Source | Document Name | Status | Key Extracted Parameters |
|---|---|---|---|
| **PMEGP** | Ministry of MSME Revised Guidelines 2022-23 (`PMEGP_REVISED_GUIDELINES_2023`) | `VERIFIED_OFFICIAL` | Max Project Cost: ₹50L (Mfg) / ₹20L (Service); Margin Money Subsidy: 35% Rural Special, 25% Rural General; Own Contribution: 5% Special, 10% General; Age ≥ 18; Education ≥ VIII pass; Udyam mandatory. |
| **PMMY / MUDRA** | MUDRA Partner Institution Eligibility (`PMMY_PARTNER_ELIGIBILITY`) | `NEEDS_SOURCE_VERIFICATION` | Document specifies partner lending institution refinance terms (Max refinance ₹20L, max 36 months). End-borrower product tiers (Shishu, Kishore, Tarun) and interest rate caps are **not present** in this source and remain unverified. |
| **AIDIS / NSO** | NSS Report No. 588, 77th Round (`AIDIS_NSS_77_REPORT_588`) | `VERIFIED_OFFICIAL` | Aggregate Karnataka Rural Debt Statistics: Incidence of Indebtedness 48.1%; 67.2% Institutional vs. 32.5% Non-Institutional; 58% of informal debt carries >20% p.a. interest. |
| **RBI PSL Master Directions** | RBI Priority Sector Lending Directions 2025 (`RBI_PSL_MASTER_DIRECTIONS_2025`) | `VERIFIED_OFFICIAL` | Bank lending compliance framework: 7.5% ANBC target for Micro-enterprises; Allied agricultural activities qualify under Agriculture PSL without limit. |

---

## 3. Architecture Distinction: Unit Cost vs. Model Project Profile

To prevent conflation of different official sources:
1. **`NABARD_UNIT_COST`**:
   - Represents statutory committee-approved average capital expenditure for agricultural and allied activities in Karnataka.
   - Sourced from NABARD SLUCC (State Level Unit Cost Committee).
   - Contains unit livestock, civil structures, and initial operational working costs.
2. **`MODEL_PROJECT_PROFILE`**:
   - Represents comprehensive institutional pre-feasibility techno-economic reports (e.g. from KVIC, MDTC, or Ministry of MSME).
   - Contains fixed capital, equipment schedules, detailed manpower headcounts, installed capacity, production costs, and projected revenues.
   - Preserves historical benchmark year (e.g., 2020 for Flour Mill) rather than presenting as current spot market prices.

---

## 4. Policy on Missing Data

- Under `REAL_DATA_ONLY=True`, queries for **Tailoring** and **Kirana** explicitly return `DATA_NOT_AVAILABLE`.
- Under legacy development/testing mode (`REAL_DATA_ONLY=False`), legacy in-memory estimates are returned with explicit provenance tags (`source_type: "SYNTHETIC_BASELINE"`, `verification_status: "SYNTHETIC"`, `is_synthetic: true`).
- No synthetic numbers are ever passed off as government-verified or NABARD-approved data.
