"""
Structured Financial Provenance and Evidence Models.
Separates SOURCE values (from NABARD, scheme guidelines, model profiles)
from DERIVED values (calculated deterministically by Python math).
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ProvenanceRecord(BaseModel):
    """
    Cryptographic and bibliographic lineage record for a single financial parameter.
    """
    parameter: str
    value: Any
    unit: str = "INR"
    source_id: Optional[str] = None
    source_organization: Optional[str] = None
    source_page: Optional[int] = None
    publication_year: Optional[int] = None
    verification_status: str  # "VERIFIED", "DATA_NOT_AVAILABLE", "NEEDS_SOURCE_VERIFICATION", "DERIVED", "SYNTHETIC"
    source_type: str          # "NABARD_UNIT_COST", "MODEL_PROJECT_PROFILE", "GOVERNMENT_SCHEME_RULE", "DERIVED_MATHEMATICAL", "APPLICATION_ASSUMPTION", "USER_INPUT"
    cost_nature: Optional[str] = None  # e.g., "HISTORICAL_BENCHMARK_2020"
    derived_from: Optional[List[str]] = None
    notes: Optional[str] = None

class FinancialEvidence(BaseModel):
    """
    Complete evidence bundle attached to a financial calculation or DPR.
    """
    source_records: List[ProvenanceRecord] = Field(default_factory=list)
    derived_records: List[ProvenanceRecord] = Field(default_factory=list)
    deviation_analysis: Optional[Dict[str, Any]] = None

    def to_provenance_table(self) -> List[Dict[str, Any]]:
        """Exports a flat tabular structure suitable for DPR and UI tables."""
        table = []
        for r in self.source_records:
            table.append({
                "parameter": r.parameter,
                "value": f"₹{r.value:,.2f}" if isinstance(r.value, (int, float)) and r.unit == "INR" else str(r.value),
                "source": r.source_organization or r.source_id or "Direct Input",
                "page": str(r.source_page) if r.source_page else "—",
                "year": str(r.publication_year) if r.publication_year else "—",
                "type": r.source_type,
                "status": r.verification_status,
                "notes": r.notes or ""
            })
        for r in self.derived_records:
            table.append({
                "parameter": r.parameter,
                "value": f"₹{r.value:,.2f}" if isinstance(r.value, (int, float)) and r.unit == "INR" else str(r.value),
                "source": "Derived by Deterministic Engine",
                "page": "—",
                "year": "—",
                "type": "DERIVED_CALCULATION",
                "status": "DETERMINISTIC_DERIVATION",
                "notes": f"Calculated from {', '.join(r.derived_from or [])}"
            })
        return table
