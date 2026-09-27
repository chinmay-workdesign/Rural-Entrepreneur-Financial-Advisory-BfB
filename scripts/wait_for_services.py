"""
Container start-up: wait until the Qdrant server answers before the app starts, so the knowledge
collection check (and the first-run ingest) runs against a live Qdrant instead of failing.
"""
import os
import sys
import time

import requests

url = os.environ.get("QDRANT_URL")
if not url:
    sys.exit(0)

for _ in range(60):
    try:
        if requests.get(f"{url.rstrip('/')}/readyz", timeout=2).ok:
            print(f"Qdrant ready at {url}")
            sys.exit(0)
    except requests.RequestException:
        pass
    time.sleep(1)

print(f"Qdrant at {url} did not become ready in 60s; starting anyway", file=sys.stderr)
