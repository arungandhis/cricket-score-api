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
# LIVE MATCHES (NEW 2024–2026 SELECTORS)
# ---------------------------------------------------------
def live_matches() -> Dict[str, Any]:
    url = f"{BASE_URL}/cricket-match/live-scores"
    soup = _soup(url)

    matches = []

    # NEW selector: each match card is an <a> with class cb-lv-scrs-well
    cards = soup.select("a.cb-lv-scrs-well")
    print(f"[CB_HTML] live cards found={len(cards)}")

    for card in cards:
        title = card.select_one(".cb-lv-scr-mtch-hdr")
        status = card.select_one(".cb-text-live, .cb-text-complete, .cb-text-preview")

        # Teams are in the first two .cb-ovr-flo elements
        team_elems = card.select(".cb-ovr-flo")
        teams = [t.get_text(strip=True) for t in team_elems[:2]]

        # Score is usually the 3rd .cb-ovr-flo
        score = team_elems[2].get_text(strip=True) if len(team_elems) > 2 else ""

        matches.append({
            "title": title.get_text(strip=True) if title else "",
            "status": status.get_text(strip=True) if status else "",
            "teams": teams,
            "score": score,
        })

    return {"matches": matches, "source": "cricbuzz_html"}


# ---------------------------------------------------------
# RECENT MATCHES (NEW SELECTORS)
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
# UPCOMING MATCHES (NEW SELECTORS)
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
# MATCH DETAILS (NEW SELECTORS)
# ---------------------------------------------------------
def match(match_id: str) -> Dict[str, Any]:
    url = f"{BASE_URL}/live-cricket-scorecard/{match_id}"
    soup = _soup(url)

    # Title
    title_el = soup.select_one("h1.cb-nav-hdr")
    title = title_el.get_text(strip=True) if title_el else "Unknown Match"

    # Status
    status_el = soup.select_one(
        ".cb-text-complete, .cb-text-stump, .cb-text-inprogress, .cb-text-live"
    )
    status = status_el.get_text(strip=True) if status_el else "Status unavailable"

    # Score (team 1 + team 2)
    score_blocks = soup.select(".cb-col.cb-col-100.cb-ltst-wgt-hdr")
    score_text = " | ".join([b.get_text(strip=True) for b in score_blocks])

    # Commentary (NEW selector)
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
