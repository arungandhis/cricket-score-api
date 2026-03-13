import json
from typing import Any, Dict
import requests

BASE_URL = "https://www.cricbuzz.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}
TIMEOUT = 10


class CricbuzzJSONError(Exception):
    pass


def _get_json(path: str) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"
    print(f"[CB_JSON] GET {url}")
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    print(f"[CB_JSON] status={resp.status_code}, content-type={resp.headers.get('Content-Type')}")

    if resp.status_code == 404:
        raise CricbuzzJSONError("Cricbuzz JSON 404 Not Found")
    if resp.status_code >= 500:
        raise CricbuzzJSONError(f"Cricbuzz JSON server error {resp.status_code}")

    content_type = resp.headers.get("Content-Type", "")
    if "application/json" not in content_type:
        try:
            data = resp.json()
            print("[CB_JSON] parsed JSON from non-JSON content-type")
            return data
        except json.JSONDecodeError:
            print("[CB_JSON] JSON decode error")
            raise CricbuzzJSONError(f"Unexpected non-JSON response (Content-Type={content_type})")

    return resp.json()


def live_matches() -> Dict[str, Any]:
    data = _get_json("/api/matches/live")
    print(f"[CB_JSON] live_matches count={len(data.get('matches', []))}")
    data["source"] = "cricbuzz_json"
    return data


def recent_matches() -> Dict[str, Any]:
    data = _get_json("/api/matches/recent")
    print(f"[CB_JSON] recent_matches count={len(data.get('matches', []))}")
    data["source"] = "cricbuzz_json"
    return data


def upcoming_matches() -> Dict[str, Any]:
    data = _get_json("/api/matches/upcoming")
    print(f"[CB_JSON] upcoming_matches count={len(data.get('matches', []))}")
    data["source"] = "cricbuzz_json"
    return data


def match(match_id: str) -> Dict[str, Any]:
    data = _get_json(f"/api/cricket-match/{match_id}")
    data["source"] = "cricbuzz_json"
    return data


def scorecard(match_id: str) -> Dict[str, Any]:
    data = _get_json(f"/api/cricket-match/{match_id}/scorecard")
    data["source"] = "cricbuzz_json"
    return data


def commentary(match_id: str) -> Dict[str, Any]:
    data = _get_json(f"/api/cricket-match/{match_id}/commentary")
    data["source"] = "cricbuzz_json"
    return data


def timeline(match_id: str) -> Dict[str, Any]:
    data = _get_json(f"/api/cricket-match/{match_id}/timeline")
    data["source"] = "cricbuzz_json"
    return data


def stats(match_id: str) -> Dict[str, Any]:
    data = _get_json(f"/api/cricket-match/{match_id}/stats")
    data["source"] = "cricbuzz_json"
    return data
