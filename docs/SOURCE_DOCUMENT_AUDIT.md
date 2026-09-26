# Source Document Audit: Raw Data Verification & Metadata Assessment

**Audit Date:** 2026-09-25  
**Directory Inspected:** `data/raw/`  
**Auditor:** Antigravity AI  

---

## 1. Master Source Inventory Table

| File | Organization | Title | Year / Date | Pages | Geography | Data Type | Intended Use | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `NABARD Karnataka UC Booklet 26_27.pdf` | NABARD (Karnataka Regional Office, Bengaluru) | Unit Cost of Investments in Agriculture & Allied Activities 2026-27 | July 2026 (2026-27) | 80 | Karnataka (State-wide) | Unit Cost / Model Project Capex & Opex | Authoritative benchmark pricing for Dairy and Poultry farm investments | **VERIFIED_OFFICIAL** |
| `PMEGP Revised Guidelines 22-23.pdf` | Ministry of MSME, Govt of India (PMEGP Section) | Approval for modifications in PMEGP guidelines making Udyam Registration mandatory for PMEGP units | 07-12-2023 (Applies to 15th FC cycle 2021-22 to 2025-26) | 29 | All-India (Rural & Urban) | Statutory Policy Guidelines & Subsidy Schedules | Primary rules for PMEGP capital margin subsidies, ceilings (₹50L / ₹20L), own contribution, and agency flow | **VERIFIED_OFFICIAL** |
| `All India Debt and Investment Survey - 2019.pdf` | National Statistical Office (NSO), MoSPI, Govt of India | NSS Report no. 588 (77/18.2): All India Debt & Investment Survey - 2019 | September 2021 (Survey period: Jan-Dec 2019) | 1,919 | All-India & All States (inc. Karnataka) | Statistical Survey Report & Aggregate Statements | Empirical evidence on rural debt, formal vs informal credit ratios, and moneylender interest rate distributions | **VERIFIED_OFFICIAL** |
| `Master Directions - Reserve Bank of India (Priority Sector Lending – Targets.pdf` | Reserve Bank of India (FIDD, Central Office, Mumbai) | Reserve Bank of India (Priority Sector Lending – Targets and Classification) Directions, 2025 | 2025 (Updated up to 2025) | 53 | All-India | Central Banking Regulatory Directions | Regulatory definitions of micro-enterprise credit, KVI treatment, and priority sector mandates | **VERIFIED_OFFICIAL** |
| `PMMY Eligibility.pdf` | Micro Units Development & Refinance Agency Limited (MUDRA) | Broad Eligibility Criteria for Partner Institutions | Undated official circular (~2023-2024) | 9 | All-India | Institutional Refinance Policy Norms | Verifies MUDRA partner bank refinance eligibility; **DOES NOT** provide individual Shishu/Kishore/Tarun borrower-facing product circular rules | **NEEDS_SOURCE_VERIFICATION** (Institutional refinance document; borrower guidelines needed) |

---

## 2. In-Depth Source Assessment

### 2.1 NABARD Karnataka UC Booklet 2026-27
* **File Path:** `data/raw/nabard/NABARD Karnataka UC Booklet 26_27.pdf`
* **Issuing Body:** Department of Refinance, NABARD Karnataka Regional Office, Kempe Gowda Road, Bengaluru. (Dr. Surendra Babu, Chief General Manager). State Level Unit Cost Committee (SLUCC) approved on 29 May 2026.
* **Content:**
  * Chapter 1: Water Resources (Pages 1-7)
  * Chapter 2: Land Development (Pages 8-12)
  * Chapter 3: Farm Mechanization (Pages 13-16)
  * Chapter 4: Plantation & Horticulture (Pages 17-24)
  * Chapter 5: Sericulture (Pages 25-28)
  * Chapter 6: Forestry (Pages 29-31)
  * Chapter 7: Animal Husbandry:
    * Dairy (Pages 32-39): Contains exact itemized costs for 2-Cow CB unit, 10-Cow unit, Indigenous breeds, calf rearing, and hydroponics.
    * Poultry (Pages 40-44): Contains itemized costs for Commercial Layer (5000 birds), Broiler (5000 birds), Backyard poultry, and Integrated Broiler (2000 & 5000 birds).
    * Sheep, Goat, Piggery (Pages 45-58)
  * Chapter 8: Fisheries and Aquaculture (Pages 59-61)
  * Chapter 9: Storage Structures (Pages 62-65)
  * Chapter 10: Renewable Energy (Pages 66-68)
* **Gap for Pilot Categories:**
  * **Dairy:** Found (2 Crossbred Cows: ₹2,29,000 for HF / ₹2,05,000 for Jersey).
  * **Poultry:** Found (2,000 Broilers under integration: ₹4,56,000; 5,000 Broilers commercial: ₹20,80,000).
  * **Tailoring:** NOT AVAILABLE in this agricultural booklet.
  * **Kirana / Grocery Store:** NOT AVAILABLE in this agricultural booklet.
  * **Flour Mill (Atta Chakki):** NOT AVAILABLE in this agricultural booklet.

### 2.2 PMEGP Revised Guidelines (2022-23 / Dec 2023)
* **File Path:** `data/raw/schemes/PMEGP Revised Guidelines 22-23.pdf`
* **Issuing Body:** Ministry of MSME, Govt of India, Office Memorandum No: PMEGP/UdhyamReg./01/2023 dated 07-12-2023.
* **Content:** Complete scheme operational guidelines governing the 15th Finance Commission cycle (2021-22 to 2025-26).
* **Extractable Hard Rules:**
  * Max project cost: ₹50 Lakhs (Manufacturing), ₹20 Lakhs (Business/Service).
  * Rural Margin Money Subsidy: 35% for Special Categories (SC/ST/OBC/Women/Minority/Transgender/Differently abled); 25% for General Category.
  * Urban Margin Money Subsidy: 25% for Special Categories; 15% for General Category.
  * Beneficiary Own Contribution: 5% (Special Categories); 10% (General Category).
  * Repayment schedule: 3 to 7 years after initial moratorium prescribed by financing bank.
  * Udyam registration is mandatory.

### 2.3 All-India Debt and Investment Survey (AIDIS) - NSS 77th Round
* **File Path:** `data/raw/aidis/All India Debt and Investment Survey - 2019.pdf`
* **Issuing Body:** National Statistical Office (NSO), MoSPI, Report No. 588.
* **Content:** Complete 1,919-page report containing Chapter 1-3 summary findings and 1,753 pages of detailed state-wise statistical tables (Appendix A).
* **Extractable Empirical Statistics for Karnataka Rural:**
  * Statement 7 (Page 92): Incidence of Indebtedness (IOI) in rural Karnataka is 48.1% (59.2% for cultivators, 32.9% for non-cultivators).
  * Statement 8 (Page 94): Outstanding cash debt breakdown: 67.2% from Institutional agencies; 32.5% from Non-Institutional agencies.
  * Statement 10 (Page 97): Rate of interest on non-institutional loans: 36.3% of non-institutional debt carries 20%-25% interest; 18.9% carries 30%-50% interest; 2.8% carries 50%-100% interest. Over 58% of non-institutional debt in rural Karnataka is charged over 20% annual interest.

### 2.4 RBI Master Directions - Priority Sector Lending (PSL)
* **File Path:** `data/raw/rbi/Master Directions - Reserve Bank of India (Priority Sector Lending – Targets.pdf`
* **Issuing Body:** Reserve Bank of India, FIDD.
* **Content:** Regulatory directions governing PSL classification for commercial banks, RRBs, Small Finance Banks, and UCBs.
* **Relevance:** Confirms that all credit to Khadi and Village Industries (KVI) sector qualifies as lending to Micro Enterprises under Priority Sector Lending.

### 2.5 PMMY Eligibility Document
* **File Path:** `data/raw/schemes/PMMY Eligibility.pdf`
* **Issuing Body:** Micro Units Development & Refinance Agency Limited (MUDRA).
* **Content:** Technical institutional eligibility criteria for partner lending institutions (Banks, SFBs, NBFC-MFIs) to draw refinance from MUDRA.
* **Assessment:** While authentic and official, this document does not contain the detailed borrower-facing guidelines for Shishu (up to ₹50k), Kishore (₹50k-₹5L), and Tarun (₹5L-₹10L/₹20L) tiers. Marked as `NEEDS_SOURCE_VERIFICATION` for scheme rules.
