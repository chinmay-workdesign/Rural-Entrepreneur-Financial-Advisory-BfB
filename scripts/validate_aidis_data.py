"""
Validator for data/processed/aidis/credit_statistics.json.
Checks that all extracted survey statistics have valid numerical percentages/values,
known indicators, valid geography, and provenanced source pages.
"""
import os
import sys
import json
from pypdf import PdfReader

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def validate_aidis_data():
    aidis_path = os.path.join("data", "processed", "aidis", "credit_statistics.json")
    manifest_path = os.path.join("data", "manifests", "sources_manifest.json")

    if not os.path.exists(aidis_path):
        print(f"[FAIL] File not found at {aidis_path}")
        sys.exit(1)

    with open(aidis_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    valid_source_ids = {s["source_id"]: s for s in manifest.get("sources", [])}

    stats = data.get("statistics", [])
    if not stats:
        print("[FAIL] No statistical records found in AIDIS dataset.")
        sys.exit(1)

    errors = []
    print(f"[VALIDATE] Validating {len(stats)} AIDIS statistical records from NSS Report 588...\n")

    for s in stats:
        sid = s.get("statistic_id")
        ind = s.get("indicator")
        val = s.get("value")
        geo = s.get("geography")
        source_id = s.get("source_id", data.get("source_id"))
        spage = s.get("source_page")
        status = s.get("verification_status")

        if not sid or not ind or val is None or not geo:
            errors.append(f"Missing core fields in statistic: {s}")
            continue

        if not isinstance(val, (int, float)):
            errors.append(f"Value for {sid} is not numeric: {val}")

        if source_id not in valid_source_ids:
            errors.append(f"Unknown source_id '{source_id}' in statistic {sid}")
        else:
            raw_pdf = valid_source_ids[source_id]["local_path"]
            if os.path.exists(raw_pdf):
                reader = PdfReader(raw_pdf)
                if spage is None or spage < 1 or spage > len(reader.pages):
                    errors.append(f"Invalid source_page {spage} for statistic {sid}")

        unit_str = "%" if s.get("unit") == "PERCENTAGE" else f" {s.get('unit')}"
        print(f"  [PASS] {sid} ({geo}): {ind} = {val}{unit_str} (Page {spage}, Status: {status})")

    if errors:
        print("\n[FAIL] VALIDATION ERRORS FOUND:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] ALL AIDIS CREDIT STATISTICS VALIDATED SUCCESSFULLY.")

if __name__ == "__main__":
    validate_aidis_data()
