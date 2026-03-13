import time
from typing import Any, Dict

from cache import cache
from providers import cricbuzz_json as cbj
from providers import cricbuzz_html as cbh
from providers import espn_html as espn


class CricketAPIError(Exception):
    pass


MAX_RETRIES = 3
BACKOFF = 1.5


def _with_retries(fn, *args, **kwargs) -> Dict[str, Any]:
    last_exc = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[RETRY] calling {fn.__name__}, attempt {attempt}")
            return fn(*args, **kwargs)
        except Exception as e:
            print(f"[RETRY] {fn.__name__} failed on attempt {attempt}: {e}")
            last_exc = e
            if attempt == MAX_RETRIES:
                break
            time.sleep(BACKOFF * attempt)

    raise CricketAPIError(str(last_exc))


def _cached(key: str, ttl: int, fn, *args, **kwargs) -> Dict[str, Any]:
    cached = cache.get(key)
    if cached is not None:
        print(f"[CACHE HIT] {key}")
        return cached

    print(f"[CACHE MISS] {key}, calling {fn.__name__}")
    data = _with_retries(fn, *args, **kwargs)
    cache.set(key, data, ttl=ttl)
    return data


def _fallback_matches(key: str, ttl: int, json_fn, html_fn, espn_fn):
    print(f"[FALLBACK_MATCHES] key={key}")

    try:
        data = _cached(f"{key}:cb_json", ttl, json_fn)
        print(f"[FALLBACK_MATCHES] cb_json returned {len(data.get('matches', []))} matches")
        if data.get("matches"):
            return data
    except Exception as e:
        print(f"[FALLBACK_MATCHES] cb_json error: {e}")

    try:
        data = _cached(f"{key}:cb_html", ttl, html_fn)
        print(f"[FALLBACK_MATCHES] cb_html returned {len(data.get('matches', []))} matches")
        if data.get("matches"):
            return data
    except Exception as e:
        print(f"[FALLBACK_MATCHES] cb_html error: {e}")

    try:
        data = _cached(f"{key}:espn_html", ttl, espn_fn)
        print(f"[FALLBACK_MATCHES] espn_html returned {len(data.get('matches', []))} matches")
        return data
    except Exception as e:
        print(f"[FALLBACK_MATCHES] espn_html error: {e}")
        raise CricketAPIError(f"All providers failed: {e}")


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
    print(f"[GET_MATCH] match_id={match_id}")

    try:
        return _cached(f"match:{match_id}:cb_json", 5, cbj.match, match_id)
    except Exception as e:
        print(f"[GET_MATCH] cb_json error: {e}")

    try:
        return _cached(f"match:{match_id}:cb_html", 5, cbh.match, match_id)
    except Exception as e:
        print(f"[GET_MATCH] cb_html error: {e}")

    try:
        return _cached(f"match:{match_id}:espn_html", 5, espn.match, match_id)
    except Exception as e:
        print(f"[GET_MATCH] espn_html error: {e}")
        raise CricketAPIError(f"All providers failed: {e}")


def get_scorecard(match_id: str) -> Dict[str, Any]:
    try:
        return _cached(f"scorecard:{match_id}:cb_json", 5, cbj.scorecard, match_id)
    except Exception as e:
        print(f"[GET_SCORECARD] cb_json error: {e}")
        return get_match(match_id)


def get_commentary(match_id: str) -> Dict[str, Any]:
    try:
        return _cached(f"commentary:{match_id}:cb_json", 3, cbj.commentary, match_id)
    except Exception as e:
        print(f"[GET_COMMENTARY] cb_json error: {e}")
        return get_match(match_id)


def get_timeline(match_id: str) -> Dict[str, Any]:
    try:
        return _cached(f"timeline:{match_id}:cb_json", 5, cbj.timeline, match_id)
    except Exception as e:
        print(f"[GET_TIMELINE] cb_json error: {e}")
        return get_match(match_id)


def get_stats(match_id: str) -> Dict[str, Any]:
    try:
        return _cached(f"stats:{match_id}:cb_json", 30, cbj.stats, match_id)
    except Exception as e:
        print(f"[GET_STATS] cb_json error: {e}")
        return get_match(match_id)


def filter_matches_by_team(matches_json: Dict[str, Any], team_name: str):
    team_name = team_name.lower()
    filtered = []

    for match in matches_json.get("matches", []):
        teams = []

        if isinstance(match, dict):
            t1 = match.get("team1") or match.get("team1_name") or {}
            t2 = match.get("team2") or match.get("team2_name") or {}

            if isinstance(t1, dict):
                teams.append(t1.get("name", "") or t1.get("sName", ""))
            else:
                teams.append(str(t1))

            if isinstance(t2, dict):
                teams.append(t2.get("name", "") or t2.get("sName", ""))
            else:
                teams.append(str(t2))

        if any(team_name in (t or "").lower() for t in teams):
            filtered.append(match)

    print(f"[FILTER] team={team_name}, matched={len(filtered)}")
    return filtered
