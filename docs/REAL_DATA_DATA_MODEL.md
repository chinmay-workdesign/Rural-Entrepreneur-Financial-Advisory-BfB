# Real Data Foundation: Canonical Data Models & Schemas

**Document Version:** 1.0.0  
**Status:** Approved for Implementation  
**Target Branch:** `real-data-migration`  

---

## 1. Architectural Principles
1. **Source Immutability:** Raw official files (PDFs, Excel, CSVs) are stored in `data/raw/` with cryptographic hashes (SHA-256) and never mutated.
2. **Deterministic Governance:** Financial calculations receive structured, verified `PolicyRule` records. No arithmetic is executed within LLMs or prompt templates.
3. **Traceable Provenance:** Every factual benchmark, scheme cap, and statistical indicator retains a foreign key to an `OfficialSource`.

---

## 2. Canonical Schemas

### 2.1 `OfficialSource`
Represents an authoritative document, publication, gazette, or circular issued by a government department or financial authority.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "OfficialSource",
  "type": "object",
  "required": [
    "source_id",
    "organization",
    "title",
    "source_type",
    "publication_year",
    "file_hash_sha256",
    "verification_status"
  ],
  "properties": {
    "source_id": {
      "type": "string",
      "description": "Unique slug identifier (e.g., NABARD_KA_UNIT_COST_2024_25)"
    },
    "organization": {
      "type": "string",
      "enum": ["NABARD", "RBI", "KVIC", "DFS_MUDRA", "MoFPI", "MoA_FW", "MSDE", "SCA_KARNATAKA", "SCA_MAHARASHTRA", "NSO_MOSPI"]
    },
    "title": { "type": "string" },
    "circular_number": { "type": ["string", "null"] },
    "source_type": {
      "type": "string",
      "enum": ["UNIT_COST_BOOKLET", "CIRCULAR", "SCHEME_GUIDELINE", "SURVEY_REPORT", "STATISTICAL_TABLE"]
    },
    "source_url": { "type": ["string", "null"], "format": "uri" },
    "publication_date": { "type": ["string", "null"], "format": "date" },
    "effective_from": { "type": ["string", "null"], "format": "date" },
    "effective_to": { "type": ["string", "null"], "format": "date" },
    "state": { "type": ["string", "null"], "default": "All-India" },
    "district": { "type": ["string", "null"], "default": "All-District" },
    "local_path": { "type": "string", "description": "Relative path inside data/raw/" },
    "file_hash_sha256": { "type": "string" },
    "version": { "type": "string", "default": "1.0" },
    "verification_status": {
      "type": "string",
      "enum": ["VERIFIED", "DATA_PENDING", "UNVERIFIED"],
      "default": "DATA_PENDING"
    },
    "verified_by": { "type": ["string", "null"] },
    "retrieved_at": { "type": "string", "format": "date-time" }
  }
}
```

---

### 2.2 `PolicyRule`
Represents an enforceable policy parameter extracted from an official scheme document.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PolicyRule",
  "type": "object",
  "required": [
    "rule_id",
    "scheme_key",
    "parameter_name",
    "parameter_type",
    "value",
    "source_id",
    "verification_status"
  ],
  "properties": {
    "rule_id": { "type": "string", "description": "e.g., PMEGP_RURAL_SPECIAL_SUBSIDY_2023" },
    "scheme_key": {
      "type": "string",
      "enum": ["MFS", "TLS", "PMEGP", "MUDRA_SHISHU", "MUDRA_KISHORE", "MUDRA_TARUN", "KCC_AHIDF", "PM_VISHWAKARMA", "PM_SVANIDHI", "PM_FME"]
    },
    "parameter_name": {
      "type": "string",
      "enum": [
        "MAX_PROJECT_COST",
        "MIN_PROJECT_COST",
        "MAX_LOAN_AMOUNT",
        "LOAN_SHARE_PCT",
        "MIN_MARGIN_PCT",
        "SUBSIDY_PCT",
        "SUBSIDY_MAX_CAP",
        "INTEREST_RATE_PCT",
        "MAX_TENURE_MONTHS",
        "MAX_MORATORIUM_MONTHS"
      ]
    },
    "parameter_type": { "type": "string", "enum": ["CURRENCY_INR", "PERCENTAGE", "MONTHS", "BOOLEAN"] },
    "value": { "type": "number" },
    "conditions": {
      "type": "object",
      "properties": {
        "geography": { "type": "string", "enum": ["RURAL", "URBAN", "ALL"] },
        "social_category": { "type": "string", "enum": ["SPECIAL", "GENERAL", "ALL"] },
        "sector": { "type": "string", "enum": ["MANUFACTURING", "SERVICE", "BUSINESS", "ALL"] }
      }
    },
    "state": { "type": "string", "default": "All-India" },
    "effective_from": { "type": ["string", "null"], "format": "date" },
    "effective_to": { "type": ["string", "null"], "format": "date" },
    "source_id": { "type": "string" },
    "source_page": { "type": ["integer", "null"] },
    "source_table": { "type": ["string", "null"] },
    "verification_status": { "type": "string", "enum": ["VERIFIED", "DATA_PENDING", "UNVERIFIED"] }
  }
}
```

---

### 2.3 `NABARDBenchmark`
Represents standard model unit capital expenditures, operating budgets, and physical asset requirements published by NABARD for bankable projects.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "NABARDBenchmark",
  "type": "object",
  "required": [
    "benchmark_id",
    "activity",
    "state",
    "year",
    "total_unit_cost",
    "source_id",
    "verification_status"
  ],
  "properties": {
    "benchmark_id": { "type": "string", "description": "e.g., NABARD_KA_DAIRY_2COW_2024" },
    "activity": { "type": "string", "description": "Primary economic trade (e.g. Dairy Farming, Poultry Broiler, Kirana)" },
    "sub_activity": { "type": ["string", "null"], "description": "e.g., 2 Crossbred Cows Unit (CBC)" },
    "state": { "type": "string", "default": "Karnataka" },
    "district": { "type": ["string", "null"], "default": "All-District" },
    "year": { "type": "string", "description": "e.g. 2024-25" },
    "unit_specification": { "type": "string", "description": "e.g. 2 Animals, 1000 Birds, 1 Powerloom" },
    "capex_breakdown": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["item_name", "estimated_cost"],
        "properties": {
          "item_name": { "type": "string" },
          "category": { "type": "string", "enum": ["CIVIL_WORKS", "MACHINERY_EQUIPMENT", "LIVESTOCK", "WORKING_CAPITAL"] },
          "quantity": { "type": ["number", "null"] },
          "unit": { "type": ["string", "null"] },
          "estimated_cost": { "type": "number" }
        }
      }
    },
    "total_unit_cost": { "type": "number" },
    "standard_working_capital": { "type": ["number", "null"] },
    "projected_dscr": { "type": ["number", "null"] },
    "source_id": { "type": "string" },
    "source_page": { "type": ["integer", "null"] },
    "source_table": { "type": ["string", "null"] },
    "verification_status": { "type": "string", "enum": ["VERIFIED", "DATA_PENDING", "UNVERIFIED"] }
  }
}
```

---

### 2.4 `CreditStatistic`
Represents empirical household debt and credit distribution metrics derived from official survey microdata (AIDIS/NSSO/RBI).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CreditStatistic",
  "type": "object",
  "required": [
    "statistic_id",
    "dataset",
    "survey_round",
    "geography",
    "indicator",
    "value",
    "source_id",
    "verification_status"
  ],
  "properties": {
    "statistic_id": { "type": "string", "description": "e.g., AIDIS_77_KA_RURAL_INFORMAL_RATE_MEDIAN" },
    "dataset": { "type": "string", "enum": ["AIDIS", "ASUSE", "RBI_REPORT_ON_CURRENCY_AND_FINANCE"] },
    "survey_round": { "type": "string", "description": "e.g. NSS 77th Round (2019)" },
    "geography": { "type": "string", "description": "e.g. Karnataka - Rural" },
    "population_group": { "type": "string", "description": "e.g. Agricultural Households / Non-Farm Enterprise Households" },
    "indicator": {
      "type": "string",
      "enum": [
        "INCIDENCE_OF_INDEBTEDNESS_PCT",
        "INSTITUTIONAL_CREDIT_SHARE_PCT",
        "NON_INSTITUTIONAL_CREDIT_SHARE_PCT",
        "MONEYLENDER_INTEREST_RATE_MEDIAN_PCT",
        "MONEYLENDER_INTEREST_RATE_IQR_PCT",
        "AVERAGE_DEBT_PER_HOUSEHOLD_INR",
        "ASSET_TURNOVER_MEDIAN_RATIO",
        "OPERATING_MARGIN_MEDIAN_PCT"
      ]
    },
    "value": { "type": "number" },
    "unit": { "type": "string", "enum": ["PERCENTAGE", "INR", "RATIO"] },
    "sample_size": { "type": ["integer", "null"] },
    "source_id": { "type": "string" },
    "source_table_or_file": { "type": "string" },
    "verification_status": { "type": "string", "enum": ["VERIFIED", "DATA_PENDING", "UNVERIFIED"] }
  }
}
```

---

### 2.5 `FinancialResult`
The immutable calculation output generated by the deterministic financial engine, with complete cryptographic provenance.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "FinancialResult",
  "type": "object",
  "required": [
    "proposal_id",
    "project_cost",
    "loan_amount",
    "beneficiary_margin",
    "interest_rate",
    "tenure_months",
    "moratorium_months",
    "monthly_emi",
    "total_interest",
    "projected_dscr",
    "policy_version",
    "benchmark_version",
    "engine_version",
    "source_ids",
    "validation_status",
    "calculated_at"
  ],
  "properties": {
    "proposal_id": { "type": "string", "format": "uuid" },
    "scheme_key": { "type": "string" },
    "project_cost": { "type": "number" },
    "loan_amount": { "type": "number" },
    "beneficiary_margin": { "type": "number" },
    "margin_percentage": { "type": "number" },
    "interest_rate": { "type": "number" },
    "tenure_months": { "type": "integer" },
    "moratorium_months": { "type": "integer" },
    "repayment_months": { "type": "integer" },
    "monthly_emi": { "type": "number" },
    "total_interest": { "type": "number" },
    "total_repayable": { "type": "number" },
    "annual_revenue_projected": { "type": "number" },
    "annual_opex_projected": { "type": "number" },
    "projected_dscr": { "type": "number" },
    "is_bankable": { "type": "boolean" },
    "policy_version": { "type": "string" },
    "benchmark_version": { "type": "string" },
    "engine_version": { "type": "string", "default": "2.0-deterministic" },
    "source_ids": {
      "type": "array",
      "items": { "type": "string" }
    },
    "validation_status": {
      "type": "string",
      "enum": ["PASSED", "POLICY_RECONCILED", "VALIDATION_FAILED"]
    },
    "calculated_at": { "type": "string", "format": "date-time" }
  }
}
```
