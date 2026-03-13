from typing import Any, Dict
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


def live_matches() -> Dict[str, Any]:
    # ESPN does not have a stable HTML live list, so return empty
    return {"matches": [], "source": "espn_html"}


def match(match_id: str) -> Dict[str, Any]:
    """
    Uses ESPN's stable JSON feed:
    https://www.espncricinfo.com/matches/engine/match/{match_id}.json
    """
    url = f"https://www.espncricinfo.com/matches/engine/match/{match_id}.json"
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

    if resp.status_code != 200:
        raise ESPNHTMLError(f"ESPN JSON error {resp.status_code}")

    data = resp.json()

    # Extract commentary (up to 100 items)
    commentary_items = []
    if "comms" in data:
        for item in data["comms"].get("comms", [])[:100]:
            text = item.get("ball", {}).get("commentary", "")
            if text:
                commentary_items.append(text)

    return {
        "title": data.get("match", {}).get("team1_name", "") + " vs " +
                 data.get("match", {}).get("team2_name", ""),
        "status": data.get("live", {}).get("status", "Unavailable"),
        "score": data.get("live", {}).get("innings", ""),
        "commentary": commentary_items,
        "source": "espn_html",
    }
