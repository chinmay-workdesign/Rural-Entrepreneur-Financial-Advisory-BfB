"""
Retrieval Contract and Evidence Data Models for Authoritative Knowledge.
Preserves cryptographic provenance, document hashes, and bibliographic source citations.
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class RetrievedEvidence(BaseModel):
    """
    Standard evidence unit returned by the authoritative retrieval layer.
    """
    chunk_id: str
    text: str
    source_id: str
    source_title: str
    source_organization: str
    source_page: int
    publication_year: Optional[int] = None
    source_type: str  # "NABARD_UNIT_COST", "MODEL_PROJECT_PROFILE", "GOVERNMENT_SCHEME_RULE", "STATISTICAL_SURVEY_REPORT", "BANKING_REGULATORY_DIRECTION"
    verification_status: str  # "VERIFIED_OFFICIAL", "NEEDS_SOURCE_VERIFICATION", "DATA_NOT_AVAILABLE"
    relevance_score: float
    document_hash: str
    cost_nature: Optional[str] = None  # e.g., "HISTORICAL_BENCHMARK_2020"
    source_url: Optional[str] = None
    geographical_scope: Optional[str] = "Karnataka / India"
    applicability: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_citation_string(self) -> str:
        """
        Formats a standard citation from evidence metadata.
        Example: [NABARD Karnataka Unit Cost Booklet 2026-27, p.41]
        """
        year_str = f" {self.publication_year}" if self.publication_year else ""
        if "NABARD" in self.source_organization:
            return f"[NABARD Karnataka Unit Cost Booklet{year_str}, p.{self.source_page}]"
        elif "SAMADHAN" in self.source_id:
            return f"[Project SAMADHAN Flour Mill Profile, 2020, p.{self.source_page}]"
        elif "PMEGP" in self.source_id:
            return f"[PMEGP Revised Guidelines 2022-23, p.{self.source_page}]"
        elif "AIDIS" in self.source_id:
            return f"[AIDIS NSS Report No. 588, p.{self.source_page}]"
        elif "RBI" in self.source_id:
            return f"[RBI PSL Master Directions 2025, p.{self.source_page}]"
        elif "PMMY" in self.source_id:
            return f"[MUDRA Partner Guidelines (Unverified for end-borrowers), p.{self.source_page}]"
        return f"[{self.source_title}, p.{self.source_page}]"
