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
resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

if resp.status_code == 404:
raise CricbuzzJSONError("Cricbuzz JSON 404")
if resp.status_code >= 500:
raise CricbuzzJSONError(f"Cricbuzz JSON {resp.status_code}")

ctype = resp.headers.get("Content-Type", "")
if "application/json" not in ctype:
try:
return resp.json()
except json.JSONDecodeError:
raise CricbuzzJSONError(f"Non-JSON response (Content-Type={ctype})")

return resp.json()

def live_matches():
data = _get_json("/api/matches/live"); data["source"]="cricbuzz_json"; return data
def recent_matches():
data = _get_json("/api/matches/recent"); data["source"]="cricbuzz_json"; return data
def upcoming_matches():
data = _get_json("/api/matches/upcoming"); data["source"]="cricbuzz_json"; return data
def match(match_id):
data = _get_json(f"/api/cricket-match/{match_id}"); data["source"]="cricbuzz_json"; return data
def scorecard(match_id):
data = _get_json(f"/api/cricket-match/{match_id}/scorecard"); data["source"]="cricbuzz_json"; return data
def commentary(match_id):
data = _get_json(f"/api/cricket-match/{match_id}/commentary"); data["source"]="cricbuzz_json"; return data
def timeline(match_id):
data = _get_json(f"/api/cricket-match/{match_id}/timeline"); data["source"]="cricbuzz_json"; return data
def stats(match_id):
data = _get_json(f"/api/cricket-match/{match_id}/stats"); data["source"]="cricbuzz_json"; return data
