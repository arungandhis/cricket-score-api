import time
from typing import Any, Dict

from cache import cache
from providers import cricbuzz_json as cbj
from providers import cricbuzz_html as cbh
from providers import espn_html as espn


class CricketAPIError(Exception):
    """Raised when all providers fail."""
    pass


MAX_RETRIES = 3
BACKOFF = 1.5


# ---------------------------------------------------------
# Retry wrapper
# ---------------------------------------------------------
def _with_retries(fn, *args, **kwargs) -> Dict[str, Any]:
    last_exc = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt == MAX_RETRIES:
                break
            time.sleep(BACKOFF * attempt)

    raise CricketAPIError(str(last_exc))


# ---------------------------------------------------------
# Cache wrapper
# ---------------------------------------------------------
def _cached(key: str, ttl: int, fn, *args, **kwargs) -> Dict[str, Any]:
    cached = cache.get(key)
    if cached is not None:
        return cached

    data = _with_retries(fn, *args, **kwargs)
    cache.set(key, data, ttl=ttl)
    return data


# ---------------------------------------------------------
# Fallback for match lists (JSON → HTML → ESPN)
# ---------------------------------------------------------
def _fallback_matches(key: str, ttl: int, json_fn, html_fn, espn_fn):
    # 1. Cricbuzz JSON
    try:
        data = _cached(f"{key}:cb_json", ttl, json_fn)
        if data.get("matches"):
            return data
    except Exception:
        pass

    # 2. Cricbuzz HTML
    try:
        data = _cached(f"{key}:cb_html", ttl, html_fn)
        if data.get("matches"):
            return data
    except Exception:
        pass

    # 3. ESPN (always empty for lists)
    try:
        return _cached(f"{key}:espn_html", ttl, espn_fn)
    except Exception as e:
        raise CricketAPIError(f"All providers failed: {e}")


# ---------------------------------------------------------
# Public API functions
# ---------------------------------------------------------

def get_live_matches() -> Dict[str, Any]:
    return _fallback_matches(
        "live_matches",
        ttl=5,
        json_fn=cbj.live_matches,
        html_fn=cbh.live_matches,
        espn_fn=espn.live_matches,
    )


def get_recent_matches() -> Dict[str, Any]:
    return _fallback_matches(
        "recent_matches",
        ttl=30,
        json_fn=cbj.recent_matches,
        html_fn=cbh.live_matches,
        espn_fn=espn.live_matches,
    )


def get_upcoming_matches() -> Dict[str, Any]:
    return _fallback_matches(
        "upcoming_matches",
        ttl=60,
        json_fn=cbj.upcoming_matches,
        html_fn=cbh.live_matches,
        espn_fn=espn.live_matches,
    )


def get_match(match_id: str) -> Dict[str, Any]:
    # 1. Cricbuzz JSON
    try:
        return _cached(f"match:{match_id}:cb_json", 5, cbj.match, match_id)
    except Exception:
        pass

    # 2. Cricbuzz HTML
    try:
        html_data = _cached(f"match:{match_id}:cb_html", 5, cbh.match, match_id)
        team1 = html_data.get("teams", ["", ""])[0] if "teams" in html_data else ""
        team2 = html_data.get("teams", ["", ""])[1] if "teams" in html_data else ""
    except Exception:
        team1 = team2 = ""

    # 3. ESPN JSON fallback
    try:
        return _cached(
            f"match:{match_id}:espn_html",
            5,
            espn.match,
            match_id,
            team1,
            team2,
        )
    except Exception as e:
        raise CricketAPIError(f"All providers failed: {e}")


def get_scorecard(match_id: str) -> Dict[str, Any]:
    try:
        return _cached(f"scorecard:{match_id}:cb_json", 5, cbj.scorecard, match_id)
    except Exception:
        return get_match(match_id)


def get_commentary(match_id: str) -> Dict[str, Any]:
    try:
        return _cached(f"commentary:{match_id}:cb_json", 3, cbj.commentary, match_id)
    except Exception:
        return get_match(match_id)


def get_timeline(match_id: str) -> Dict[str, Any]:
    try:
        return _cached(f"timeline:{match_id}:cb_json", 5, cbj.timeline, match_id)
    except Exception:
        return get_match(match_id)


def get_stats(match_id: str) -> Dict[str, Any]:
    try:
        return _cached(f"stats:{match_id}:cb_json", 30, cbj.stats, match_id)
    except Exception:
        return get_match(match_id)
