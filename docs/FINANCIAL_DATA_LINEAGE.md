# Financial Data Lineage & Provenance Registry

This registry tracks the origin, computation type, and lineage of all financial parameters used across the financial calculation engine, debt structuring, and DPR generation in **Rural Enterprise Advisor**.

## 1. Classification of Parameter Types

1. **Directly Sourced (Official Benchmark)**: Taken directly from official NABARD unit cost publications or institutional model project profiles.
2. **Directly Sourced (Government Scheme Rule)**: Sourced from official gazetted guidelines or circulars (e.g. Ministry of MSME PMEGP).
3. **Derived (Deterministic Calculation)**: Computed via exact mathematical or financial equations (e.g., standard amortization, DSCR formula). Not provided directly by government documents.
4. **Application Assumption**: Policy/modeling assumptions made by the advisory platform to configure conservative baselines.
5. **Synthetic Baseline (Temporary)**: Legacy hardcoded values pending real-data ingestion.

---

## 2. Lineage Table

| Parameter | Current Value / Formula | Lineage Type | Source Name & ID | Source Page | Publication / Effective Date | Direct or Derived |
|---|---|---|---|---|---|---|
| **Dairy Project Cost (2 Crossbred Cows HF)** | ₹2,29,000.00 | Official Benchmark | NABARD Karnataka UC Booklet (`NABARD_KA_UC_BOOKLET_2026_27`) | Page 41, Table 1 | 2026-07-01 (Effective 2026-27) | Directly Sourced |
| **Dairy Project Cost (2 Crossbred Cows Jersey)** | ₹2,05,000.00 | Official Benchmark | NABARD Karnataka UC Booklet (`NABARD_KA_UC_BOOKLET_2026_27`) | Page 41, Table 1 | 2026-07-01 (Effective 2026-27) | Directly Sourced |
| **Dairy Livestock Component Cost** | ₹1,70,000 (HF) / ₹1,50,000 (Jersey) | Official Benchmark | NABARD Karnataka UC Booklet (`NABARD_KA_UC_BOOKLET_2026_27`) | Page 41, Table 1 | 2026-07-01 (Effective 2026-27) | Directly Sourced |
| **Dairy Civil Shed Component Cost** | ₹32,500.00 | Official Benchmark | NABARD Karnataka UC Booklet (`NABARD_KA_UC_BOOKLET_2026_27`) | Page 41, Table 1 | 2026-07-01 (Effective 2026-27) | Directly Sourced |
| **Dairy Animal Insurance** | 6.0% on livestock cost | Official Benchmark | NABARD Karnataka UC Booklet (`NABARD_KA_UC_BOOKLET_2026_27`) | Page 41, Table 1 | 2026-07-01 (Effective 2026-27) | Directly Sourced |
| **Poultry Broiler Cost (2000 Integration)** | ₹4,56,000.00 | Official Benchmark | NABARD Karnataka UC Booklet (`NABARD_KA_UC_BOOKLET_2026_27`) | Page 50, Table 8 | 2026-07-01 (Effective 2026-27) | Directly Sourced |
| **Poultry Broiler Cost (5000 Commercial)** | ₹20,80,000.00 | Official Benchmark | NABARD Karnataka UC Booklet (`NABARD_KA_UC_BOOKLET_2026_27`) | Page 49, Table 7 | 2026-07-01 (Effective 2026-27) | Directly Sourced |
| **Sheep Rearing (10+1 Bannur Breed)** | ₹1,11,000.00 | Official Benchmark | NABARD Karnataka UC Booklet (`NABARD_KA_UC_BOOKLET_2026_27`) | Page 56, Table 2 | 2026-07-01 (Effective 2026-27) | Directly Sourced |
| **Sheep Rearing (10+1 Local Breed)** | ₹98,000.00 | Official Benchmark | NABARD Karnataka UC Booklet (`NABARD_KA_UC_BOOKLET_2026_27`) | Page 56, Table 2 | 2026-07-01 (Effective 2026-27) | Directly Sourced |
| **Goat Rearing (10+1 Improved Breed)** | ₹1,13,000.00 | Official Benchmark | NABARD Karnataka UC Booklet (`NABARD_KA_UC_BOOKLET_2026_27`) | Page 60, Table 6 | 2026-07-01 (Effective 2026-27) | Directly Sourced |
| **Goat Rearing (10+1 Local Breed)** | ₹95,000.00 | Official Benchmark | NABARD Karnataka UC Booklet (`NABARD_KA_UC_BOOKLET_2026_27`) | Page 60, Table 6 | 2026-07-01 (Effective 2026-27) | Directly Sourced |
| **Piggery (3+1 Rearing cum Fattening)** | ₹1,64,000.00 | Official Benchmark | NABARD Karnataka UC Booklet (`NABARD_KA_UC_BOOKLET_2026_27`) | Page 64, Table 8 | 2026-07-01 (Effective 2026-27) | Directly Sourced |
| **Fisheries (1 Ha Freshwater Pond Culture)** | ₹8,29,000.00 | Official Benchmark | NABARD Karnataka UC Booklet (`NABARD_KA_UC_BOOKLET_2026_27`) | Page 68, Table 1 | 2026-07-01 (Effective 2026-27) | Directly Sourced |
| **Beekeeping (10 Colony Apiary Unit)** | ₹62,800.00 | Official Benchmark | NABARD Karnataka UC Booklet (`NABARD_KA_UC_BOOKLET_2026_27`) | Page 30, Table 6 | 2026-07-01 (Effective 2026-27) | Directly Sourced |
| **Sericulture (1 Ha Mulberry Garden)** | ₹2,25,000.00 | Official Benchmark | NABARD Karnataka UC Booklet (`NABARD_KA_UC_BOOKLET_2026_27`) | Page 34, Table 1 | 2026-07-01 (Effective 2026-27) | Directly Sourced |
| **Flour Mill Total Project Cost** | ₹32,93,000.00 | Official Model Profile | Project SAMADHAN Pre-Feasibility Report (`SAMADHAN_FLOUR_MILL_PROJECT_PROFILE`) | Page 5, Table 10 | 2020-01-04 (Benchmark Year 2020) | Directly Sourced |
| **Flour Mill Plant & Machinery Cost** | ₹23,84,000.00 (39 items) | Official Model Profile | Project SAMADHAN Pre-Feasibility Report (`SAMADHAN_FLOUR_MILL_PROJECT_PROFILE`) | Pages 5–7, Section 12 | 2020-01-04 (Benchmark Year 2020) | Directly Sourced |
| **Flour Mill Working Capital Margin** | ₹5,56,000.00 | Official Model Profile | Project SAMADHAN Pre-Feasibility Report (`SAMADHAN_FLOUR_MILL_PROJECT_PROFILE`) | Page 5, Table 10 | 2020-01-04 (Benchmark Year 2020) | Directly Sourced |
| **Flour Mill Annual Turnover (at 60% capacity)** | ₹3,05,85,600.00 (1440 MT) | Official Model Profile | Project SAMADHAN Pre-Feasibility Report (`SAMADHAN_FLOUR_MILL_PROJECT_PROFILE`) | Page 8, Section 13(ii) | 2020-01-04 (Benchmark Year 2020) | Directly Sourced |
| **PMEGP Manufacturing Max Cost Ceiling** | ₹50,00,000.00 | Scheme Rule | Ministry of MSME Revised Guidelines (`PMEGP_REVISED_GUIDELINES_2023`) | Page 5, Para 3.1 | 2023-12-07 | Directly Sourced |
| **PMEGP Service/Business Max Cost Ceiling** | ₹20,00,000.00 | Scheme Rule | Ministry of MSME Revised Guidelines (`PMEGP_REVISED_GUIDELINES_2023`) | Page 5, Para 3.1 | 2023-12-07 | Directly Sourced |
| **PMEGP Rural Special Margin Money Subsidy** | 35.0% of project cost | Scheme Rule | Ministry of MSME Revised Guidelines (`PMEGP_REVISED_GUIDELINES_2023`) | Page 4, Para 3.2(i) Table | 2023-12-07 | Directly Sourced |
| **PMEGP Rural Special Own Contribution** | 5.0% of project cost | Scheme Rule | Ministry of MSME Revised Guidelines (`PMEGP_REVISED_GUIDELINES_2023`) | Page 4, Para 3.2(i) Table | 2023-12-07 | Directly Sourced |
| **PMEGP Rural General Margin Money Subsidy** | 25.0% of project cost | Scheme Rule | Ministry of MSME Revised Guidelines (`PMEGP_REVISED_GUIDELINES_2023`) | Page 4, Para 3.2(i) Table | 2023-12-07 | Directly Sourced |
| **PMEGP Rural General Own Contribution** | 10.0% of project cost | Scheme Rule | Ministry of MSME Revised Guidelines (`PMEGP_REVISED_GUIDELINES_2023`) | Page 4, Para 3.2(i) Table | 2023-12-07 | Directly Sourced |
| **PMEGP Bank Loan Proportion** | Project Cost - Subsidy - Own Contribution | Scheme Rule / Formula | Ministry of MSME Revised Guidelines (`PMEGP_REVISED_GUIDELINES_2023`) | Page 5, Note 3 | 2023-12-07 | Derived (Rule-based) |
| **PMEGP Repayment Tenure** | 3 to 7 years (36 to 84 months) | Scheme Rule | Ministry of MSME Revised Guidelines (`PMEGP_REVISED_GUIDELINES_2023`) | Page 10, Para 8 | 2023-12-07 | Directly Sourced |
| **Equated Monthly Installment (EMI)** | $P \cdot r \cdot \frac{(1+r)^n}{(1+r)^n - 1}$ | Derived Calculation | Deterministic Financial Engine (`app/finance/calculator.py`) | N/A | Current | Derived (Mathematical) |
| **Debt Service Coverage Ratio (DSCR)** | $\frac{\text{Net Operating Income}}{\text{Annual Debt Service}}$ | Derived Calculation | Deterministic Financial Engine (`app/finance/dscr.py`) | N/A | Current | Derived (Financial) |
| **Benchmarked Working Capital Requirement** | $0.20 \times \text{Project Cost}$ (or itemized profile) | Application Assumption | Standard Banking Tandon/Nayak Committee Norm | N/A | Current | Application Assumption |
| **Tailoring Project Cost (Legacy)** | ₹75,000.00 | Synthetic Baseline | `app/finance/benchmarks.py` (`NABARD_BENCHMARKS[2]`) | N/A | Legacy Synthetic | Synthetic Baseline |
| **Kirana Project Cost (Legacy)** | ₹80,000.00 | Synthetic Baseline | `app/finance/benchmarks.py` (`NABARD_BENCHMARKS[0]`) | N/A | Legacy Synthetic | Synthetic Baseline |

---

## 3. Safety Invariants

1. **Calculated values must NEVER be attributed to government documents**: EMI, DSCR, and annual interest totals are derived by deterministic software routines; they do not appear as static constants in NABARD booklets or PMEGP guidelines.
2. **Historical profiles must NEVER be masqueraded as current prices**: Model project profiles (such as Samadhan Flour Mill 2020) must preserve their publication year.
3. **Absence must NEVER be masked by synthetic figures**: If `REAL_DATA_ONLY=True`, activities without an authoritative source must return `DATA_NOT_AVAILABLE`.
