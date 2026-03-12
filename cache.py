import time
from typing import Any, Dict, Optional

class TTLCache:
def __init__(self, default_ttl: int = 10):
self.default_ttl = default_ttl
self._store: Dict[str, Any] = {}
self._expiry: Dict[str, float] = {}

def get(self, key: str) -> Optional[Any]:
now = time.time()
if key in self._store and self._expiry.get(key, 0) > now:
return self._store[key]
if key in self._store:
self._store.pop(key, None)
self._expiry.pop(key, None)
return None

def set(self, key: str, value: Any, ttl: Optional[int] = None):
if ttl is None:
ttl = self.default_ttl
self._store[key] = value
self._expiry[key] = time.time() + ttl

cache = TTLCache(default_ttl=10)
