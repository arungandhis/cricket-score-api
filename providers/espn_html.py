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
    print("[ESPN] live_matches called (returns empty by design)")
    return {"matches": [], "source": "espn_html"}


def match(match_id: str) -> Dict[str, Any]:
    url = f"https://www.espncricinfo.com/matches/engine/match/{match_id}.json"
    print(f"[ESPN] GET {url}")
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    print(f"[ESPN] status={resp.status_code}")

    if resp.status_code != 200:
        raise ESPNHTMLError(f"ESPN JSON error {resp.status_code}")

    data = resp.json()
    print(f"[ESPN] keys={list(data.keys())[:10]}")

    commentary_items = []
    if "comms" in data:
        for item in data["comms"].get("comms", [])[:100]:
            text = item.get("ball", {}).get("commentary", "")
            if text:
                commentary_items.append(text)

    return {
        "title": "ESPN Match",
        "status": data.get("live", {}).get("status", "Unavailable"),
        "score": data.get("live", {}).get("innings", ""),
        "commentary": commentary_items,
        "source": "espn_html",
    }
