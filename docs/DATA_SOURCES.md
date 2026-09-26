# Official Data Sources Registry & Acquisition Manifest

**Document Version:** 1.0.0  
**Target Pilot Scope:** Karnataka (Dairy, Poultry, Tailoring, Kirana, Flour Mill)  
**Verification Policy:** No third-party blogs, aggregator summaries, or unofficial financial portals. Only official publications with SHA-256 hashes are admitted.

---

## 1. Government Scheme Sources

### 1.1 Prime Minister's Employment Generation Programme (PMEGP)
* **Authoritative Issuing Body:** Khadi and Village Industries Commission (KVIC), Ministry of Micro, Small and Medium Enterprises (MoMSME), Government of India.
* **Official Document:** *PMEGP Scheme Operational Guidelines (Updated Amendment 2022-23)*
* **Official Portal:** `https://www.kviconline.gov.in`
* **Target Raw File:** `data/raw/schemes/PMEGP_Operational_Guidelines_2022_23.pdf`
* **Governing Rules to Extract:**
  * Maximum Project Outlay for Manufacturing: ₹50,00,000
  * Maximum Project Outlay for Service/Business: ₹20,00,000
  * Rural Margin Money Subsidy (Special Category - SC/ST/OBC/Women/Minority): 35%
  * Rural Margin Money Subsidy (General Category): 25%
  * Beneficiary Own Contribution: 5% (Special) / 10% (General)
* **Verification Status:** `DATA_PENDING` (Document pending ingestion into `data/raw/schemes/`)

### 1.2 Pradhan Mantri MUDRA Yojana (PMMY)
* **Authoritative Issuing Body:** Department of Financial Services (DFS), Ministry of Finance, Government of India.
* **Official Document:** *PMMY Scheme Guidelines & Credit Guarantee Fund for Micro Units (CGFMU) Rules*
* **Official Portal:** `https://www.mudra.org.in` & `https://www.jansamarth.in`
* **Target Raw File:** `data/raw/schemes/PMMY_Guidelines_DFS.pdf`
* **Governing Rules to Extract:**
  * Shishu Tier: Loans up to ₹50,000 (No margin required)
  * Kishore Tier: Loans from ₹50,001 to ₹5,00,000 (Margin norm: 15%)
  * Tarun Tier: Loans from ₹5,00,001 to ₹10,00,000 (Expanded to ₹20,00,000 under Tarun Plus in Union Budget 2024 for entrepreneurs who have repaid earlier loans)
* **Verification Status:** `DATA_PENDING`

### 1.3 State Channelizing Agency (Karnataka State Minorities / Backward Classes Development Corporations)
* **Authoritative Issuing Body:** Karnataka Minorities Development Corporation (KMDC) / D. Devaraj Urs Backward Classes Development Corporation, Government of Karnataka.
* **Official Document:** *Citizen Charter & Lending Guidelines for Micro Finance Scheme (MFS) and Term Loan Scheme (TLS)*
* **Official Portal:** `https://kmdc.karnataka.gov.in`
* **Target Raw File:** `data/raw/schemes/KMDC_DDUBCDC_Lending_Guidelines_KA.pdf`
* **Governing Rules to Extract:**
  * Annual Family Income Ceiling: Rural limit vs Urban limit
  * MFS Ceiling, Loan Cap, and Concessional Interest Rate
  * TLS Ceiling, Loan Cap, and Concessional Interest Rate
  * Mandatory Moratorium and Repayment Tenure Schedules
* **Verification Status:** `DATA_PENDING`

### 1.4 Animal Husbandry Infrastructure Development Fund (AHIDF) & KCC Animal Husbandry
* **Authoritative Issuing Body:** Department of Animal Husbandry and Dairying, Ministry of Fisheries, Animal Husbandry & Dairying, Government of India.
* **Official Document:** *Kisan Credit Card (KCC) for Animal Husbandry and Fisheries Working Capital Guidelines & Interest Subvention Notifications*
* **Official Portal:** `https://dahd.nic.in`
* **Target Raw File:** `data/raw/schemes/KCC_Animal_Husbandry_Guidelines_MoA.pdf`
* **Verification Status:** `DATA_PENDING`

---

## 2. NABARD Benchmark Sources

### 2.1 NABARD Karnataka State Unit Cost Booklet
* **Authoritative Issuing Body:** National Bank for Agriculture and Rural Development (NABARD), Karnataka Regional Office, State Development Policy Department (DPD), Bengaluru.
* **Official Document:** *Unit Costs for Investment in Agriculture and Allied Activities for Karnataka (2024-25)*
* **Official Portal:** `https://www.nabard.org`
* **Target Raw File:** `data/raw/nabard/NABARD_Karnataka_Unit_Cost_2024_25.pdf`
* **Target Activities for Initial Migration:**
  1. **Dairy:** 2 Crossbred Cows (CBC) / Murrah Buffaloes Unit including shed construction, animal cost, insurance, and equipment.
  2. **Poultry:** Commercial Broiler Unit (1,000 birds batch) including deep litter shed, feeding equipment, and day-old chicks.
  3. **Tailoring / Off-Farm Micro:** Non-Farm Sector (NFS) micro-enterprise model profiles.
  4. **Flour Mill / Agro-Processing:** Small-scale commercial Atta Chakki / grain destoner unit.
* **Verification Status:** `DATA_PENDING`

### 2.2 Potential Linked Credit Plans (PLPs)
* **Authoritative Issuing Body:** NABARD District Development Offices (e.g. Belagavi, Mysuru, Mandya).
* **Official Document:** *Potential Linked Credit Plan (PLP) 2024-25: District Chapter on Micro, Small and Medium Enterprises (MSME) & Allied Activities*
* **Target Raw File:** `data/raw/nabard/PLP_2024_25_Belagavi.pdf`
* **Verification Status:** `DATA_PENDING`

---

## 3. AIDIS / NSO Survey Sources

### 3.1 All-India Debt and Investment Survey (AIDIS) - NSS 77th Round
* **Authoritative Issuing Body:** National Statistical Office (NSO), Ministry of Statistics and Programme Implementation (MoSPI), Government of India.
* **Survey Round:** NSS 77th Round (January 2019 – December 2019), Schedule 18.2: *Debt and Investment*.
* **Official Report:** *NSS Report No. 588: Indebtedness of Rural Households*
* **Official Portal:** `https://mospi.gov.in`
* **Target Raw File:** `data/raw/aidis/NSS_77_Report_588_Indebtedness_Rural_Households.pdf`
* **Target Survey Metrics to Extract for Karnataka Rural:**
  * Percentage of households indebted.
  * Share of debt from Institutional Sources (Commercial Banks, RRBs, Cooperative Banks).
  * Share of debt from Non-Institutional Sources (Agricultural/Professional Moneylenders, Relatives/Friends).
  * Weighted average and distribution of interest rates charged by professional moneylenders in rural areas (used for cost-of-capital comparison).
* **Verification Status:** `DATA_PENDING`

### 3.2 Annual Survey of Unincorporated Sector Enterprises (ASUSE)
* **Authoritative Issuing Body:** National Statistical Office (NSO), MoSPI.
* **Official Report:** *Annual Survey of Unincorporated Sector Enterprises (ASUSE) 2021-22 & 2022-23 Factsheets*
* **Target Raw File:** `data/raw/aidis/ASUSE_Report_Micro_Enterprises.pdf`
* **Target Survey Metrics to Extract:**
  * Gross Value Added (GVA) per worker for rural retail trade (NIC 47), food manufacturing (NIC 10), and garment manufacturing (NIC 14).
  * Statistical operating expense ratios to replace the flat `65%` assumption.
* **Verification Status:** `DATA_PENDING`

---

## 4. Reserve Bank of India (RBI) Sources

### 4.1 Master Direction – Priority Sector Lending (PSL) – Targets and Classification
* **Authoritative Issuing Body:** Financial Inclusion and Development Department, Reserve Bank of India.
* **Official Document:** *RBI/FIDD/2020-21/72 Master Direction FIDD.MSME.BC.No.01/06.02.031/2020-21*
* **Official Portal:** `https://www.rbi.org.in`
* **Target Raw File:** `data/raw/rbi/RBI_Master_Direction_PSL_Targets.pdf`
* **Governing Rules to Extract:**
  * Mandatory PSL targets for Micro-Enterprises (7.5% of ANBC).
  * Collateral-free lending limits for micro-enterprises under RBI directions.
* **Verification Status:** `DATA_PENDING`

---

## 5. Pilot Target Matrix (Initial Phase)

| Sector | Target Activity | Geographic Scope | Primary Policy Document | Primary Benchmark Document | Statistical Validation Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Livestock** | Small Dairy Unit (2 Cows) | Karnataka (Belagavi / Mysuru) | KCC Animal Husbandry / SCA MFS | NABARD KA Unit Cost 2024-25 (Table 2.1) | AIDIS NSS 77 (Livestock Households) |
| **Allied Agri** | Poultry Broiler (1,000 birds) | Karnataka (Mandya / Belagavi) | NABARD PVCF / SCA TLS | NABARD KA Unit Cost 2024-25 (Table 2.3) | ASUSE NIC 014 (Poultry farming) |
| **Manufacturing**| Tailoring / Garment Stitching | Karnataka | PM Vishwakarma / PMEGP / MFS | NABARD Off-Farm Sector Model Profiles | ASUSE NIC 141 (Manufacture of wearing apparel) |
| **Retail Trade** | Kirana / Village Grocery | Karnataka | PM SVANidhi / PMMY Kishore / MFS | Model Retail Project Profile | ASUSE NIC 471 (Retail in non-specialized stores) |
| **Agro-Processing**| Mini Flour Mill (Atta Chakki) | Karnataka | PM-FME / PMEGP / TLS | NABARD Agro-Processing Model Profile | ASUSE NIC 106 (Grain mill products) |
