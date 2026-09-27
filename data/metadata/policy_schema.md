# Policy Rules Data Dictionary & Schema

**Dataset Target:** `data/processed/schemes/*.json` (e.g. `pmegp_rules.json`, `pmmy_rules.json`)  
**Governing Documents:** Ministry of MSME, DFS, and State SCA Operational Guidelines  

---

## Field Specifications

| Field | Meaning | Datatype | Allowed Values | Source & Provenance Requirement |
| :--- | :--- | :--- | :--- | :--- |
| `rule_id` | Unique policy rule slug | String | e.g. `PMEGP_MARGIN_MONEY_SUBSIDY_RURAL_SPECIAL` | Unique across all government schemes |
| `parameter` | Parameter classification | String | `MAX_PROJECT_COST`, `SUBSIDY_PCT`, `OWN_CONTRIBUTION_MIN_PCT`, `REPAYMENT_TENURE_YEARS`, `MIN_AGE`, `MIN_EDUCATION`, etc. | Standard policy parameter taxonomy |
| `sector` | Eligible sector | String / Null | `MANUFACTURING`, `SERVICE_OR_BUSINESS`, `ALL` | As restricted by scheme guidelines |
| `area` | Location of project unit | String / Null | `RURAL`, `URBAN`, `ALL` | As defined in scheme policy table |
| `category` | Social/promoter demographic | String / Null | `SPECIAL`, `GENERAL`, `ALL` | Explicit definitions (e.g. SC/ST/OBC/Women) |
| `value` | Parameter numerical value | Float / Integer / String | e.g. `35.0`, `5000000.0`, `VIII Standard Pass` | Strict statutory amount or percentage |
| `unit` | Dimensional measurement unit | String | `INR`, `PERCENTAGE_OF_PROJECT_COST`, `YEARS`, `PERSON_PER_FAMILY`, `CALCULATED` | Dimensional unit identifier |
| `conditions` | Detailed operational condition | String | Free-form legal/policy condition | Verbatim or summarized from circular text |
| `source_id` | Foreign key to manifest | String | Must exist in `sources_manifest.json` | Mandatory foreign key |
| `source_page` | Physical page in PDF | Integer | 1 to total pages (e.g. `4`, `5`, `10`) | Verified PDF reader page number |
| `section` | Document paragraph / section | String | e.g. `Para 3.2(i) Table`, `Para 4.1` | Exact clause reference |
| `verification_status`| Authenticity status | String | `VERIFIED`, `NEEDS_SOURCE_VERIFICATION`, `DATA_PENDING` | Must be `VERIFIED` to govern financial calculations |
