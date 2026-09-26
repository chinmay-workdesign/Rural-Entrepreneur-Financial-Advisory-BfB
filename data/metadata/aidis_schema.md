# AIDIS Credit Statistics Data Dictionary & Schema

**Dataset Target:** `data/processed/aidis/credit_statistics.json`  
**Governing Document:** National Statistical Office (NSO) NSS Report No. 588  

---

## Field Specifications

| Field | Meaning | Datatype | Allowed Values | Source & Provenance Requirement |
| :--- | :--- | :--- | :--- | :--- |
| `statistic_id` | Unique statistical slug | String | e.g. `AIDIS_KA_RURAL_IOI_ALL`, `AIDIS_KA_RURAL_INFORMAL_ROI_20_TO_25` | Follows pattern: `AIDIS_<STATE>_<SECTOR>_<INDICATOR>` |
| `indicator` | Official survey indicator | String | `INCIDENCE_OF_INDEBTEDNESS_PCT`, `OUTSTANDING_CASH_DEBT_SHARE_PCT`, `NON_INSTITUTIONAL_DEBT_ROI_SHARE_PCT`, etc. | Uses exact NSO survey terminology |
| `credit_agency_type`| Agency categorization | String / Null | `INSTITUTIONAL_AGENCIES`, `NON_INSTITUTIONAL_AGENCIES` | Strict AIDIS two-tier classification |
| `interest_rate_bracket`| Informal interest tier | String / Null | `NIL (INTEREST FREE)`, `20% - 25% P.A.`, `30% - 50% P.A.`, etc. | Matches Statement 10 intervals |
| `geography` | State / Region | String | `Karnataka`, `All-India` | State name as tabulated by NSO |
| `sector` | Rural vs Urban | String | `RURAL`, `URBAN` | Rural/Urban stratum |
| `population_category`| Occupational class | String / Null | `ALL_HOUSEHOLDS`, `CULTIVATOR_HOUSEHOLDS`, `NON_CULTIVATOR_HOUSEHOLDS` | Official household occupational categories |
| `value` | Numerical value | Float | e.g. `48.1`, `67.2`, `36.3` | Exact weighted percentage from report |
| `unit` | Unit of measurement | String | `PERCENTAGE`, `INR` | Dimension identifier |
| `source_id` | Foreign key to manifest | String | Must exist in `sources_manifest.json` | Mandatory foreign key |
| `source_page` | Physical page in PDF | Integer | 1 to total pages (e.g. `92`, `94`, `97`) | Verified PDF reader page number |
| `table_reference` | Summary statement title | String | e.g. `Statement 7`, `Statement 8`, `Statement 10` | Exact table caption in report |
| `verification_status`| Authenticity status | String | `VERIFIED`, `UNVERIFIED` | Must be `VERIFIED` to enter analytics layer |
