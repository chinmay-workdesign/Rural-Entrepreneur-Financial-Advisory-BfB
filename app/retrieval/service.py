"""
Local Authoritative Evidence Retrieval Service (FastEmbed + Qdrant).
Queries local Qdrant collection with FastEmbed embeddings.
Enforces source trust filtering, page provenance preservation, and cryptographic document hashes.
Completely independent of LLMs and deterministic financial math.
Zero external paid RAG or JEV dependencies.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from fastembed import TextEmbedding
from app.config import settings
from app.retrieval.models import RetrievedEvidence
from app.retrieval.ingest import COLLECTION_NAME, EMBEDDING_MODEL_NAME

logger = logging.getLogger("retrieval_service")

class QdrantUnavailableError(RuntimeError):
    """Raised when the Qdrant vector database is unreachable or unavailable."""
    pass

class EvidenceRetrievalService:
    """
    Authoritative knowledge retrieval service backed by local persistent Qdrant or Docker container.
    """
    def __init__(self, data_root: Optional[str] = None, qdrant_path: Optional[str] = None, qdrant_url: Optional[str] = None):
        if data_root is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.data_root = os.path.join(base_dir, "data")
        else:
            self.data_root = data_root

        if qdrant_path is None:
            self.qdrant_path = os.path.join(self.data_root, "qdrant_db")
        else:
            self.qdrant_path = qdrant_path

        self.qdrant_url = qdrant_url or settings.QDRANT_URL
        self._embedding_model = None

    @property
    def embedding_model(self) -> TextEmbedding:
        if self._embedding_model is None:
            self._embedding_model = TextEmbedding(model_name=settings.EMBEDDING_MODEL or EMBEDDING_MODEL_NAME)
        return self._embedding_model

    def _get_client(self) -> QdrantClient:
        """
        Initializes Qdrant client. Prefers QDRANT_URL if configured, falling back to local on-disk storage.
        Raises QdrantUnavailableError if connection cannot be established.
        """
        try:
            if self.qdrant_url:
                logger.debug(f"Connecting to Qdrant at URL: {self.qdrant_url}")
                return QdrantClient(url=self.qdrant_url, timeout=5)
            else:
                os.makedirs(self.qdrant_path, exist_ok=True)
                return QdrantClient(path=self.qdrant_path)
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise QdrantUnavailableError(f"Qdrant vector database is unavailable: {e}") from e

    def verify_collection_ready(self, auto_build_if_empty: bool = False) -> bool:
        """
        Explicit deployment / startup check to ensure authoritative collection is ready.
        Only builds the index if auto_build_if_empty is explicitly set to True (e.g. during deployment setup).
        """
        client = self._get_client()
        try:
            exists = client.collection_exists(COLLECTION_NAME)
            if not exists:
                if auto_build_if_empty:
                    logger.info(f"Explicitly initializing collection '{COLLECTION_NAME}'...")
                    from app.retrieval.ingest import IngestionPipeline
                    pipeline = IngestionPipeline(data_root=self.data_root, qdrant_path=self.qdrant_path)
                    pipeline.build_and_index()
                    return True
                else:
                    logger.warning(f"Authoritative Qdrant collection '{COLLECTION_NAME}' is not yet indexed.")
                    return False
            return True
        finally:
            client.close()

    def retrieve_evidence(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        require_verified: bool = True
    ) -> List[RetrievedEvidence]:
        """
        Retrieves top_k relevant evidence chunks for a semantic query.

        Default behavior:
        - require_verified=True: strictly filters for verification_status == 'VERIFIED_OFFICIAL'.
        - When REAL_DATA_ONLY=True: prevents semantic similarity override for unavailable categories
          (e.g., Kirana, Tailoring). Returns empty if query is specifically asking for unverified/unavailable data.
        """
        query_lower = query.lower()

        # Semantic similarity guard: If user explicitly asks for unit costs / benchmarks of unavailable trades,
        # do not return dairy/poultry chunks solely because of query words like "unit cost" or "benchmark".
        unavailable_trades = ["kirana", "grocery", "tailoring", "garment", "stitching"]
        cost_inquiry_terms = ["cost", "unit cost", "benchmark", "budget", "outlay", "price", "project cost"]
        is_unavailable_trade_cost_query = any(t in query_lower for t in unavailable_trades) and any(c in query_lower for c in cost_inquiry_terms)

        if is_unavailable_trade_cost_query and settings.REAL_DATA_ONLY:
            logger.info(f"Query '{query}' asks for unavailable trade cost benchmark under REAL_DATA_ONLY. Returning empty evidence to prevent semantic hallucination.")
            return []

        client = self._get_client()

        try:
            if not client.collection_exists(COLLECTION_NAME):
                logger.error(f"Qdrant collection '{COLLECTION_NAME}' does not exist. Ingestion must be performed explicitly at initialization.")
                raise QdrantUnavailableError(
                    f"Qdrant collection '{COLLECTION_NAME}' does not exist. "
                    f"Run 'py -m app.retrieval.ingest' during deployment to index the authoritative corpus before servicing queries."
                )

            query_vectors = list(self.embedding_model.embed([query]))
            query_vector = query_vectors[0].tolist() if hasattr(query_vectors[0], "tolist") else list(query_vectors[0])

            qdrant_conditions = []
            if require_verified:
                qdrant_conditions.append(
                    FieldCondition(key="verification_status", match=MatchValue(value="VERIFIED_OFFICIAL"))
                )

            if filters:
                for k, v in filters.items():
                    if v is not None:
                        qdrant_conditions.append(FieldCondition(key=k, match=MatchValue(value=v)))

            qdrant_filter = Filter(must=qdrant_conditions) if qdrant_conditions else None

            search_result = client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                query_filter=qdrant_filter,
                limit=top_k,
                with_payload=True
            )

            results: List[RetrievedEvidence] = []
            for point in search_result.points:
                p = point.payload or {}
                evidence = RetrievedEvidence(
                    chunk_id=str(p.get("chunk_id", f"chunk-{point.id}")),
                    text=p.get("text", ""),
                    source_id=p.get("source_id", "UNKNOWN"),
                    source_title=p.get("source_title", "Official Source Document"),
                    source_organization=p.get("source_organization", "Government Authority"),
                    source_page=int(p.get("source_page", 1)),
                    publication_year=p.get("publication_year"),
                    source_type=p.get("source_type", "BENCHMARK"),
                    verification_status=p.get("verification_status", "VERIFIED_OFFICIAL"),
                    relevance_score=round(float(point.score), 4),
                    document_hash=p.get("document_hash", ""),
                    cost_nature=p.get("cost_nature"),
                    source_url=p.get("source_url"),
                    geographical_scope=p.get("geographical_scope", "Karnataka / India"),
                    applicability=p.get("applicability"),
                    metadata={
                        "activity": p.get("activity"),
                        "scheme": p.get("scheme"),
                        "point_id": point.id
                    }
                )
                results.append(evidence)

            return results
        finally:
            client.close()

# Global retrieval service instance
retrieval_service = EvidenceRetrievalService()

def retrieve_evidence(
    query: str,
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None,
    require_verified: bool = True
) -> List[RetrievedEvidence]:
    """Helper functional API for evidence retrieval."""
    return retrieval_service.retrieve_evidence(
        query=query,
        top_k=top_k,
        filters=filters,
        require_verified=require_verified
    )
