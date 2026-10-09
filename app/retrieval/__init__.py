"""
Local Authoritative Knowledge Retrieval (FastEmbed + Qdrant).
"""
from .models import RetrievedEvidence
from .service import EvidenceRetrievalService, retrieval_service, retrieve_evidence, QdrantUnavailableError
from .context_builder import build_grounded_llm_messages, GROUNDED_SYSTEM_INSTRUCTIONS
from .ingest import IngestionPipeline
from .router import QueryIntent, classify_query_intent, execute_authoritative_routing
from .serpapi_client import SerpApiClient, serpapi_client

__all__ = [
    "RetrievedEvidence",
    "EvidenceRetrievalService",
    "retrieval_service",
    "retrieve_evidence",
    "QdrantUnavailableError",
    "build_grounded_llm_messages",
    "GROUNDED_SYSTEM_INSTRUCTIONS",
    "IngestionPipeline",
    "QueryIntent",
    "classify_query_intent",
    "execute_authoritative_routing",
    "SerpApiClient",
    "serpapi_client",
]
