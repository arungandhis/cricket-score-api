from typing import Any, Dict, List, Optional
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.espncricinfo.com/",
}
TIMEOUT = 10


class ESPNHTMLError(Exception):
    pass


# ---------------------------------------------------------
# ESPN MATCH ID LOOKUP
# ---------------------------------------------------------
def find_espn_match_id(team1: str, team2: str) -> Optional[str]:
    """
    Uses ESPN's search API to find the correct ESPN match ID.
    """
    query = f"{team1} {team2}"
    url = f"https://site.web.api.espn.com/apis/search/v2?query={query}"

    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    if resp.status_code != 200:
        return None

    data = resp.json()

    for item in data.get("results", []):
        if "match" in item.get("type", "").lower():
            return item.get("id")

    return None


# ---------------------------------------------------------
# ESPN DOES NOT PROVIDE A RELIABLE LIVE MATCH LIST
# ---------------------------------------------------------
def live_matches() -> Dict[str, Any]:
    return {"matches": [], "source": "espn_html"}


# ---------------------------------------------------------
# ESPN MATCH DETAILS + COMMENTARY (JSON FEED)
# ---------------------------------------------------------
def match(match_id: str, team1: str = "", team2: str = "") -> Dict[str, Any]:
    """
    Uses ESPN's stable JSON feed:
    https://www.espncricinfo.com/matches/engine/match/{espn_id}.json
    """

    # Step 1: Map Cricbuzz ID → ESPN ID
    espn_id = find_espn_match_id(team1, team2)
    if not espn_id:
        return {"matches": [], "source": "espn_html"}

    url = f"https://www.espncricinfo.com/matches/engine/match/{espn_id}.json"
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

    if resp.status_code != 200:
        raise ESPNHTMLError(f"ESPN JSON error {resp.status_code}")

    data = resp.json()

    # Commentary
    commentary_items = []
    if "comms" in data:
        for item in data["comms"].get("comms", [])[:100]:
            text = item.get("ball", {}).get("commentary", "")
            if text:
                commentary_items.append(text)

    return {
        "title": f"{team1} vs {team2}",
        "status": data.get("live", {}).get("status", "Unavailable"),
        "score": data.get("live", {}).get("innings", ""),
        "commentary": commentary_items,
        "source": "espn_html",
    }
