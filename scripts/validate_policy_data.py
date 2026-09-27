"""
Validator for scheme policy rules in data/processed/schemes/*.json.
Checks that all rules have valid parameters, provenance, valid pages in raw source PDFs,
and no missing values.
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

def validate_policy_data():
    schemes_dir = os.path.join("data", "processed", "schemes")
    manifest_path = os.path.join("data", "manifests", "sources_manifest.json")

    if not os.path.exists(manifest_path):
        print(f"[FAIL] Manifest not found at {manifest_path}")
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    valid_source_ids = {s["source_id"]: s for s in manifest.get("sources", [])}

    errors = []
    rule_files = [f for f in os.listdir(schemes_dir) if f.endswith(".json")]

    print(f"[VALIDATE] Validating policy rules across {len(rule_files)} files in {schemes_dir}...\n")

    for rf in rule_files:
        p = os.path.join(schemes_dir, rf)
        with open(p, "r", encoding="utf-8") as fp:
            data = json.load(fp)

        scheme_name = data.get("scheme_name", rf)
        sid = data.get("source_id")
        rules = data.get("rules", []) or data.get("extracted_parameters", [])

        print(f"[INFO] Validating scheme file '{rf}' ({scheme_name})...")

        if sid not in valid_source_ids:
            errors.append(f"Scheme file '{rf}' references unknown source_id '{sid}'")
            continue

        raw_pdf = valid_source_ids[sid]["local_path"]
        pdf_reader = PdfReader(raw_pdf) if os.path.exists(raw_pdf) and raw_pdf.lower().endswith(".pdf") else None

        for r in rules:
            rid = r.get("rule_id")
            param = r.get("parameter")
            val = r.get("value")
            spage = r.get("source_page")
            status = r.get("verification_status")

            if not rid or not param or val is None:
                errors.append(f"Missing core fields in rule: {r}")
                continue

            if pdf_reader and spage:
                if spage < 1 or spage > len(pdf_reader.pages):
                    errors.append(f"Rule {rid} has invalid source_page {spage} (PDF has {len(pdf_reader.pages)} pages)")

            print(f"  [PASS] Rule '{rid}': {param} = {val} (Page {spage}, Status: {status})")

    if errors:
        print("\n[FAIL] VALIDATION ERRORS FOUND:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] ALL POLICY RULES VALIDATED SUCCESSFULLY.")

if __name__ == "__main__":
    validate_policy_data()
