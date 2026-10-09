"""
SerpApi Web Search & Live Market Grounding Client.
Fetches real-time market data, trade benchmarks, and scheme details from Google Search via SerpApi.
Includes TTL caching to preserve API quotas and minimizes latency.
"""
import time
import hashlib
import logging
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional

import httpx

from app.config import settings
from app.retrieval.models import RetrievedEvidence

logger = logging.getLogger("serpapi_client")


class SerpApiClient:
    BASE_URL = "https://serpapi.com/search.json"

    def __init__(self, api_key: Optional[str] = None, ttl_seconds: int = 86400):
        self._explicit_key = api_key is not None
        self.api_key = api_key if api_key is not None else getattr(settings, "SERPAPI_API_KEY", "")
        self.ttl_seconds = ttl_seconds
        # In-memory cache: {cache_key: (timestamp, results)}
        self._cache: Dict[str, tuple[float, List[Dict[str, Any]]]] = {}

    def is_configured(self) -> bool:
        """Returns True if SerpApi is enabled and an API key is present."""
        if self._explicit_key:
            return bool(self.api_key and self.api_key.strip())
        key = self.api_key or getattr(settings, "SERPAPI_API_KEY", "")
        enabled = getattr(settings, "SERPAPI_ENABLED", True)
        return bool(enabled and key and key.strip())

    def _get_cache_key(self, query: str, engine: str, location: str) -> str:
        key_str = f"{engine}:{location}:{query.strip().lower()}"
        return hashlib.sha256(key_str.encode("utf-8")).hexdigest()

    def search_raw(
        self,
        query: str,
        max_results: int = 3,
        engine: str = "google",
        timeout: float = 35.0
    ) -> List[Dict[str, Any]]:
        """
        Executes a synchronous Google search via SerpApi with India geolocation.
        Returns extracted items (title, snippet, link, source).
        """
        if not self.is_configured():
            logger.debug("SerpApi is not configured or disabled; returning empty results.")
            return []

        location = getattr(settings, "SERPAPI_SEARCH_LOCATION", "Karnataka,India")
        cache_key = self._get_cache_key(query, engine, location)

        # Check Cache
        now = time.time()
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if now - cached_time < self.ttl_seconds:
                logger.info(f"SerpApi cache hit for query: '{query}'")
                return cached_data

        params = {
            "engine": engine,
            "q": query,
            "gl": "in",
            "hl": "en",
            "location": location,
            "api_key": self.api_key,
            "num": max_results,
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(self.BASE_URL, params=params)
                if resp.status_code != 200:
                    logger.warning(f"SerpApi returned HTTP {resp.status_code}: {resp.text[:200]}")
                    return []
                data = resp.json()

            extracted = self._extract_results(data, max_results)
            # Store in cache
            self._cache[cache_key] = (now, extracted)
            return extracted

        except Exception as e:
            logger.warning(f"SerpApi search failed for query '{query}': {e}")
            return []

    async def search_raw_async(
        self,
        query: str,
        max_results: int = 3,
        engine: str = "google",
        timeout: float = 35.0
    ) -> List[Dict[str, Any]]:
        """Asynchronous variant of search_raw."""
        if not self.is_configured():
            return []

        location = getattr(settings, "SERPAPI_SEARCH_LOCATION", "Karnataka,India")
        cache_key = self._get_cache_key(query, engine, location)

        now = time.time()
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if now - cached_time < self.ttl_seconds:
                return cached_data

        params = {
            "engine": engine,
            "q": query,
            "gl": "in",
            "hl": "en",
            "location": location,
            "api_key": self.api_key,
            "num": max_results,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(self.BASE_URL, params=params)
                if resp.status_code != 200:
                    logger.warning(f"SerpApi async returned HTTP {resp.status_code}: {resp.text[:200]}")
                    return []
                data = resp.json()

            extracted = self._extract_results(data, max_results)
            self._cache[cache_key] = (now, extracted)
            return extracted
        except Exception as e:
            logger.warning(f"SerpApi async search failed for query '{query}': {e}")
            return []

    def _extract_results(self, data: Dict[str, Any], max_results: int) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        # 1. Answer Box or Knowledge Graph
        answer_box = data.get("answer_box", {})
        if answer_box:
            snippet = (
                answer_box.get("snippet")
                or answer_box.get("answer")
                or "\n".join(answer_box.get("list", []))
            )
            title = answer_box.get("title") or "Direct Answer"
            link = answer_box.get("link") or ""
            if snippet:
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "link": link,
                    "type": "answer_box"
                })

        # 2. Organic Results
        for item in data.get("organic_results", []):
            if len(results) >= max_results:
                break
            snippet = item.get("snippet", "")
            title = item.get("title", "")
            link = item.get("link", "")
            if snippet or title:
                results.append({
                    "title": title,
                    "snippet": snippet,
                    "link": link,
                    "type": "organic"
                })

        return results

    def search_as_evidence(
        self,
        query: str,
        max_results: int = 3,
        search_prompt_context: Optional[str] = None
    ) -> List[RetrievedEvidence]:
        """
        Searches SerpApi and formats the items into standard RetrievedEvidence objects.
        """
        # Keep search query clean and concise for Google search
        full_query = query.strip()
        raw_results = self.search_raw(full_query, max_results=max_results)
        evidence_list: List[RetrievedEvidence] = []

        for idx, res in enumerate(raw_results, 1):
            title = res.get("title") or "Live Web Result"
            snippet = res.get("snippet") or ""
            link = res.get("link") or ""
            domain = urlparse(link).netloc if link else "Web Search"

            chunk_id = hashlib.sha256(f"{link}_{snippet}".encode("utf-8")).hexdigest()[:16]
            doc_hash = hashlib.sha256(snippet.encode("utf-8")).hexdigest()

            evidence = RetrievedEvidence(
                chunk_id=f"serpapi_{chunk_id}",
                text=f"{title}\n{snippet}",
                source_id=f"SERPAPI_{domain.replace('.', '_')}",
                source_title=title,
                source_organization=domain or "Live Web Search",
                source_page=1,
                publication_year=2026,
                source_type="SERPAPI_WEB_SEARCH",
                verification_status="LIVE_WEB_SEARCH",
                relevance_score=0.85,
                document_hash=doc_hash,
                source_url=link,
                geographical_scope=getattr(settings, "SERPAPI_SEARCH_LOCATION", "Karnataka, India"),
                metadata={"url": link, "domain": domain, "type": res.get("type", "organic")}
            )
            evidence_list.append(evidence)

        return evidence_list


# Singleton instance
serpapi_client = SerpApiClient()
