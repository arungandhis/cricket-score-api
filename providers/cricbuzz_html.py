from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.cricbuzz.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 10


class CricbuzzHTMLError(Exception):
    pass


# ---------------------------------------------------------
# Internal helper
# ---------------------------------------------------------
def _soup(url: str) -> BeautifulSoup:
    print(f"[CB_HTML] GET {url}")
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    print(f"[CB_HTML] status={resp.status_code}")
    if resp.status_code != 200:
        raise CricbuzzHTMLError(f"Cricbuzz HTML error {resp.status_code}")
    return BeautifulSoup(resp.text, "html.parser")


# ---------------------------------------------------------
# LIVE MATCHES — TEMP DEBUG VERSION
# ---------------------------------------------------------
def live_matches() -> Dict[str, Any]:
    url = f"{BASE_URL}/cricket-match/live-scores"
    print(f"[CB_HTML] LIVE URL {url}")

    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    print("[CB_HTML] live status:", resp.status_code)

    # 🔍 KEY DEBUG: dump first 1000 chars of HTML so we can see real structure
    snippet = resp.text[:1000]
    print("[CB_HTML] live first 1000 chars:\n", snippet)

    # Still parse it so function shape stays the same
    soup = BeautifulSoup(resp.text, "html.parser")

    matches: List[Dict[str, Any]] = []

    # Keep a very generic selector for now; we’ll refine after seeing HTML
    cards = soup.select("a.cb-lv-scrs-well, div.cb-mtch-lst, div.cb-col-100")
    print("[CB_HTML] live cards found (generic selector):", len(cards))

    return {"matches": matches, "source": "cricbuzz_html"}


# ---------------------------------------------------------
# RECENT MATCHES (leave as‑is for now)
# ---------------------------------------------------------
def recent_matches() -> Dict[str, Any]:
    url = f"{BASE_URL}/cricket-match/live-scores/recent-matches"
    soup = _soup(url)

    matches = []
    cards = soup.select("a.cb-lv-scrs-well")
    print(f"[CB_HTML] recent cards found={len(cards)}")

    for card in cards:
        title = card.select_one(".cb-lv-scr-mtch-hdr")
        status = card.select_one(".cb-text-complete")

        team_elems = card.select(".cb-ovr-flo")
        teams = [t.get_text(strip=True) for t in team_elems[:2]]
        score = team_elems[2].get_text(strip=True) if len(team_elems) > 2 else ""

        matches.append({
            "title": title.get_text(strip=True) if title else "",
            "status": status.get_text(strip=True) if status else "",
            "teams": teams,
            "score": score,
        })

    return {"matches": matches, "source": "cricbuzz_html"}


# ---------------------------------------------------------
# UPCOMING MATCHES (leave as‑is for now)
# ---------------------------------------------------------
def upcoming_matches() -> Dict[str, Any]:
    url = f"{BASE_URL}/cricket-match/live-scores/upcoming-matches"
    soup = _soup(url)

    matches = []
    cards = soup.select("a.cb-lv-scrs-well")
    print(f"[CB_HTML] upcoming cards found={len(cards)}")

    for card in cards:
        title = card.select_one(".cb-lv-scr-mtch-hdr")

        team_elems = card.select(".cb-ovr-flo")
        teams = [t.get_text(strip=True) for t in team_elems[:2]]

        matches.append({
            "title": title.get_text(strip=True) if title else "",
            "teams": teams,
            "status": "Upcoming",
            "score": "",
        })

    return {"matches": matches, "source": "cricbuzz_html"}


# ---------------------------------------------------------
# MATCH DETAILS (leave as‑is for now)
# ---------------------------------------------------------
def match(match_id: str) -> Dict[str, Any]:
    url = f"{BASE_URL}/live-cricket-scorecard/{match_id}"
    soup = _soup(url)

    title_el = soup.select_one("h1.cb-nav-hdr")
    title = title_el.get_text(strip=True) if title_el else "Unknown Match"

    status_el = soup.select_one(
        ".cb-text-complete, .cb-text-stump, .cb-text-inprogress, .cb-text-live"
    )
    status = status_el.get_text(strip=True) if status_el else "Status unavailable"

    score_blocks = soup.select(".cb-col.cb-col-100.cb-ltst-wgt-hdr")
    score_text = " | ".join([b.get_text(strip=True) for b in score_blocks])

    commentary_items = [
        c.get_text(strip=True)
        for c in soup.select(".cb-com-ln")[:100]
    ]

    print(f"[CB_HTML] match {match_id}: score_blocks={len(score_blocks)}, commentary={len(commentary_items)}")

    return {
        "title": title,
        "status": status,
        "score": score_text,
        "commentary": commentary_items,
        "source": "cricbuzz_html",
    }
