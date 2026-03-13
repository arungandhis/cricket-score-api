import requests
from typing import Dict, Any

BASE_URL = "https://www.cricbuzz.com/api"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}
TIMEOUT = 10


class CricbuzzJSONError(Exception):
    pass


def _get(path: str) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

    if resp.status_code != 200:
        raise CricbuzzJSONError(f"HTTP {resp.status_code}")

    return resp.json()


def live_matches() -> Dict[str, Any]:
    data = _get("/cricket/live")
    data["source"] = "cricbuzz_json"
    return data


def recent_matches() -> Dict[str, Any]:
    data = _get("/cricket/recent")
    data["source"] = "cricbuzz_json"
    return data


def upcoming_matches() -> Dict[str, Any]:
    data = _get("/cricket/upcoming")
    data["source"] = "cricbuzz_json"
    return data


def match(match_id: str) -> Dict[str, Any]:
    data = _get(f"/cricket-match/{match_id}")
    data["source"] = "cricbuzz_json"
    return data


def scorecard(match_id: str) -> Dict[str, Any]:
    data = _get(f"/cricket-match/{match_id}/scorecard")
    data["source"] = "cricbuzz_json"
    return data


def commentary(match_id: str) -> Dict[str, Any]:
    data = _get(f"/cricket-match/{match_id}/commentary")
    data["source"] = "cricbuzz_json"
    return data


def timeline(match_id: str) -> Dict[str, Any]:
    data = _get(f"/cricket-match/{match_id}/timeline")
    data["source"] = "cricbuzz_json"
    return data


def stats(match_id: str) -> Dict[str, Any]:
    data = _get(f"/cricket-match/{match_id}/stats")
    data["source"] = "cricbuzz_json"
    return data
