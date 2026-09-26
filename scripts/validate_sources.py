"""
Validator for data/manifests/sources_manifest.json.
Checks that all registered source documents physically exist in data/raw/
and that their SHA-256 hashes strictly match the files on disk.
"""
import os
import sys
import json
import hashlib

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def validate_sources():
    manifest_path = os.path.join("data", "manifests", "sources_manifest.json")
    if not os.path.exists(manifest_path):
        print(f"[FAIL] Manifest not found at {manifest_path}")
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sources = data.get("sources", [])
    if not sources:
        print("[FAIL] Manifest has no sources registered.")
        sys.exit(1)

    errors = []
    print(f"[VALIDATE] Validating {len(sources)} sources in {manifest_path}...\n")

    for s in sources:
        sid = s.get("source_id")
        lpath = s.get("local_path")
        expected_hash = s.get("sha256")
        status = s.get("verification_status")

        if not sid or not lpath or not expected_hash:
            errors.append(f"Missing mandatory fields in source: {s}")
            continue

        if not os.path.exists(lpath):
            errors.append(f"Source file missing on disk: {lpath} (source_id: {sid})")
            continue

        with open(lpath, "rb") as fp:
            computed_hash = hashlib.sha256(fp.read()).hexdigest()

        if computed_hash != expected_hash:
            errors.append(
                f"Hash mismatch for {sid}:\n"
                f"  Expected: {expected_hash}\n"
                f"  Computed: {computed_hash}"
            )
        else:
            print(f"  [PASS] {sid}: File verified on disk (SHA256: {computed_hash[:16]}..., Status: {status})")

    if errors:
        print("\n[FAIL] VALIDATION ERRORS FOUND:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] ALL SOURCES VERIFIED SUCCESSFULLY.")

if __name__ == "__main__":
    validate_sources()
