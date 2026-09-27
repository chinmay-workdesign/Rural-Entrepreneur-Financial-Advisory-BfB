"""
Qdrant collection readiness on fresh clones / ephemeral deploys.

1. A collection that exists in metadata but holds no points is NOT ready
2. With auto-build enabled, the empty collection is rebuilt and becomes ready
"""
import os
import shutil

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.retrieval.ingest import COLLECTION_NAME, VECTOR_DIMENSION
from app.retrieval.service import EvidenceRetrievalService

REPO_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _empty_collection_workspace(tmp_path):
    """Temp data root with the real manifest and an existing-but-empty collection."""
    data_root = tmp_path / "data"
    (data_root / "manifests").mkdir(parents=True)
    (data_root / "processed").mkdir()
    shutil.copy(os.path.join(REPO_DATA, "manifests", "sources_manifest.json"), data_root / "manifests")

    qdrant_path = str(data_root / "qdrant_db")
    client = QdrantClient(path=qdrant_path)
    client.create_collection(COLLECTION_NAME, vectors_config=VectorParams(size=VECTOR_DIMENSION, distance=Distance.COSINE))
    client.close()
    return str(data_root), qdrant_path


def _point_count(qdrant_path):
    client = QdrantClient(path=qdrant_path)
    try:
        return client.count(COLLECTION_NAME).count
    finally:
        client.close()


# 1. Existing-but-empty collection is not ready
def test_empty_collection_is_not_ready(tmp_path):
    data_root, qdrant_path = _empty_collection_workspace(tmp_path)
    service = EvidenceRetrievalService(data_root=data_root, qdrant_path=qdrant_path, qdrant_url=None)
    service.qdrant_url = None  # force embedded mode even if QDRANT_URL is configured

    assert service.verify_collection_ready(auto_build_if_empty=False) is False
    assert _point_count(qdrant_path) == 0


# 2. Auto-build fills an empty collection
def test_empty_collection_is_rebuilt_when_auto_build_enabled(tmp_path):
    data_root, qdrant_path = _empty_collection_workspace(tmp_path)
    service = EvidenceRetrievalService(data_root=data_root, qdrant_path=qdrant_path, qdrant_url=None)
    service.qdrant_url = None

    assert service.verify_collection_ready(auto_build_if_empty=True) is True
    assert _point_count(qdrant_path) > 0
