from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.cricbuzz.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 10


class CricbuzzHTMLError(Exception):
    """Raised when Cricbuzz HTML scraping fails."""
    pass


# ---------------------------------------------------------
# Internal helper to fetch and parse HTML
# ---------------------------------------------------------
def _soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    if resp.status_code != 200:
        raise CricbuzzHTMLError(f"Cricbuzz HTML error {resp.status_code}")
    return BeautifulSoup(resp.text, "html.parser")


# ---------------------------------------------------------
# Live matches (HTML fallback)
# ---------------------------------------------------------
def live_matches() -> Dict[str, Any]:
    url = f"{BASE_URL}/cricket-match/live-scores"
    soup = _soup(url)

    matches: List[Dict[str, Any]] = []

    for card in soup.select(".cb-mtch-lst"):
        title_el = card.select_one(".cb-lv-scr-mtch-hdr")
        status_el = card.select_one(".cb-text-live, .cb-text-complete, .cb-text-preview")

        teams = [
            t.get_text(strip=True)
            for t in card.select(".cb-ovr-flo.cb-hmscg-tm-nm")
        ]

        score_el = card.select_one(".cb-ovr-flo.cb-hmscg-tm-nm + .cb-ovr-flo")
        score = score_el.get_text(strip=True) if score_el else ""

        matches.append(
            {
                "title": title_el.get_text(strip=True) if title_el else "",
                "status": status_el.get_text(strip=True) if status_el else "",
                "teams": teams,
                "score": score,
            }
        )

    return {"matches": matches, "source": "cricbuzz_html"}


# ---------------------------------------------------------
# Match details (HTML fallback)
# ---------------------------------------------------------
def match(match_id: str) -> Dict[str, Any]:
    """
    Supports both live and archived matches using:
    https://www.cricbuzz.com/live-cricket-scorecard/{match_id}
    """
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

    # Score
    score_el = soup.select_one(".cb-min-bat-rw")
    score = score_el.get_text(strip=True) if score_el else "Score unavailable"

    # Commentary (up to 100 lines)
    commentary_list = [
        item.get_text(strip=True)
        for item in soup.select(".cb-col.cb-col-90.cb-com-ln")[:100]
    ]

    return {
        "title": title,
        "status": status,
        "score": score,
        "commentary": commentary_list,
        "source": "cricbuzz_html",
    }
