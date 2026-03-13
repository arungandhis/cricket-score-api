import time
from typing import Any, Dict, Optional


class TTLCache:
    """
    Simple in‑memory TTL cache.
    Used to reduce load on Cricbuzz/ESPN and speed up responses.
    """

    def __init__(self, default_ttl: int = 10):
        self.default_ttl = default_ttl
        self._store: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Returns cached value if not expired.
        Otherwise returns None.
        """
        now = time.time()

        if key in self._store and self._expiry.get(key, 0) > now:
            return self._store[key]

        # Expired → remove it
        if key in self._store:
            self._store.pop(key, None)
            self._expiry.pop(key, None)

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Stores a value with TTL.
        """
        if ttl is None:
            ttl = self.default_ttl

        self._store[key] = value
        self._expiry[key] = time.time() + ttl


# Global cache instance
cache = TTLCache(default_ttl=10)
