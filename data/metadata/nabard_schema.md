# NABARD Benchmark Data Dictionary & Schema

**Dataset Target:** `data/processed/nabard/karnataka_benchmarks.json`  
**Governing Document:** NABARD Karnataka Unit Cost of Investments in Agriculture & Allied Activities Booklet  

---

## Field Specifications

| Field | Meaning | Datatype | Allowed Values | Source & Provenance Requirement |
| :--- | :--- | :--- | :--- | :--- |
| `benchmark_id` | Unique slug identifier | String | e.g. `NABARD_KA_DAIRY_2COW_HF_2026_27` | Must follow pattern: `NABARD_<STATE>_<TRADE>_<SPEC>_<YEAR>` |
| `activity` | Broad economic trade | String | `Dairy Farming`, `Poultry Farming`, etc. | Must match official chapter/trade headings |
| `sub_activity` | Exact specification/breed/system | String | e.g. `2 Crossbred Cows (HF)`, `Commercial Broiler 2000` | Exact table line title from booklet |
| `state` | Indian State | String | `Karnataka` (for pilot) | State of issuing NABARD Regional Office |
| `district` | Specific district if differentiated | String / Null | null (state-wide) or specific district name | As specified in SLUCC circular |
| `year` | Operational year | String | e.g. `2026-27` | Official booklet fiscal year |
| `unit` | Physical capacity | String | e.g. `2 Animals`, `2000 Birds` | Required capacity basis |
| `quantity` | Numeric unit count | Integer / Float | e.g. `2`, `2000` | Scalable quantity metric |
| `cost_breakdown` | Itemized line items | Array of Objects | Array of `{item_name, category, amount}` | Every line item in NABARD table must be preserved |
| `cost_breakdown[].category` | Asset classification | String | `LIVESTOCK`, `CIVIL_STRUCTURE`, `EQUIPMENT`, `WATER_INFRASTRUCTURE`, `WORKING_CAPITAL`, `RECURRING_FEED`, `RECURRING_INSURANCE`, `RECURRING_FODDER`, `RECURRING_MISC` | Must categorize capex vs opex |
| `unit_cost` | Total benchmark unit investment | Float | Numeric > 0 (e.g. `229000.0`) | Must strictly match table total |
| `total_cost` | Total project cost | Float | Numeric > 0 | Equals `unit_cost * quantity` |
| `repayment_period` | Standard bank repayment term | String | e.g. `5 years` | As approved by SLUCC |
| `grace_period` | Standard moratorium | String | e.g. `6 months`, `None specified` | Prescribed grace period |
| `source_id` | Foreign key to manifest | String | Must exist in `sources_manifest.json` | Mandatory foreign key |
| `source_page` | Physical page in PDF | Integer | 1 to total pages (e.g. `41`, `50`) | Verified PDF reader page number |
| `chapter` | Chapter heading in booklet | String | e.g. `Chapter 7 - Animal Husbandry` | Exact chapter text |
| `table_reference` | Official table heading | String | e.g. `Table 1. Dairy- Two Animal unit` | Exact table caption |
| `verification_status`| Authenticity status | String | `VERIFIED`, `DATA_PENDING`, `DATA_NOT_AVAILABLE` | Must be `VERIFIED` to enter production engine |
