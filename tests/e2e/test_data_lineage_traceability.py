import json
import os
import pytest
from app.retrieval.router import execute_authoritative_routing

"""
Phase 7 Step 8: Cryptographic Data Lineage & Provenance Traceability.
Verifies that every authoritative retrieval answer is fully traceable:
User question
-> retrieved record
-> source_id
-> source document
-> source page
-> publication year
-> SHA-256 manifest entry
"""

def load_manifest():
    manifest_path = os.path.join("data", "manifests", "sources_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_dairy_data_lineage_to_manifest():
    """
    Trace dairy query through retrieval to physical source document and SHA-256 hash.
    """
    manifest = load_manifest()
    manifest_sources = {s["source_id"]: s for s in manifest["sources"]}

    res = execute_authoritative_routing("What is the official NABARD unit cost for 2 cows in Karnataka?", language="english")
    assert res["retrieval_used"] is True
    assert len(res["evidence"]) > 0

    first_ev = res["evidence"][0]
    source_id = first_ev["source_id"]

    # 1. Assert source_id exists in manifest
    assert source_id in manifest_sources
    source_meta = manifest_sources[source_id]

    # 2. Trace metadata
    assert source_id == "NABARD_KA_UC_BOOKLET_2026_27"
    assert first_ev["source_page"] in [41, 42]
    assert first_ev["publication_year"] == 2026

    # 3. Assert document hash matches SHA-256 in manifest
    assert first_ev["document_hash"] == source_meta["sha256"]
    assert len(first_ev["document_hash"]) == 64

    # 4. Assert physical file exists at local_path
    assert os.path.exists(source_meta["local_path"])

def test_flour_mill_data_lineage_to_manifest():
    """
    Trace Flour Mill non-farm project profile to Project SAMADHAN manifest entry.
    """
    manifest = load_manifest()
    manifest_sources = {s["source_id"]: s for s in manifest["sources"]}

    res = execute_authoritative_routing("What is the official project cost for a flour mill?", language="english")
    assert res["retrieval_used"] is True

    # Find the SAMADHAN chunk
    flour_chunks = [e for e in res["evidence"] if "FLOUR_MILL" in e["chunk_id"] or "SAMADHAN" in e["source_id"]]
    assert len(flour_chunks) > 0

    ev = flour_chunks[0]
    assert ev["source_id"] in manifest_sources
    source_meta = manifest_sources[ev["source_id"]]

    assert ev["source_id"] == "SAMADHAN_FLOUR_MILL_PROJECT_PROFILE"
    assert ev["source_page"] == 5
    assert ev["publication_year"] == 2020
    assert ev["cost_nature"] == "HISTORICAL_BENCHMARK_2020"
    assert ev["document_hash"] == source_meta["sha256"]
    assert os.path.exists(source_meta["local_path"])

def test_aidis_data_lineage_to_manifest():
    """
    Trace AIDIS aggregate credit query to NSS Report 588 manifest entry.
    """
    manifest = load_manifest()
    manifest_sources = {s["source_id"]: s for s in manifest["sources"]}

    res = execute_authoritative_routing("What share of rural household debt came from institutional sources in AIDIS?", language="english")
    assert res["retrieval_used"] is True

    aidis_chunks = [e for e in res["evidence"] if "AIDIS" in e["source_id"]]
    assert len(aidis_chunks) > 0

    ev = aidis_chunks[0]
    source_meta = manifest_sources[ev["source_id"]]
    assert ev["source_id"] == "AIDIS_NSS_77_REPORT_588"
    assert ev["source_page"] in [92, 94]
    assert ev["document_hash"] == source_meta["sha256"]
    assert os.path.exists(source_meta["local_path"])
