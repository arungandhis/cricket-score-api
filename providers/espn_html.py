from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.espncricinfo.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 10

class ESPNHTMLError(Exception):
pass

def _soup(url: str):
resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
if resp.status_code != 200:
raise ESPNHTMLError(f"ESPN HTML {resp.status_code}")
return BeautifulSoup(resp.text, "html.parser")

def live_matches():
url = f"{BASE_URL}/live-cricket-score"
soup = _soup(url)
matches=[]
for card in soup.select(".ds-px-4.ds-py-3"):
title_el = card.select_one(".ds-text-tight-m")
status_el = card.select_one(".ds-text-tight-s")
score_el = card.select_one(".ds-text-compact-s")
matches.append({
"title": title_el.get_text(strip=True) if title_el else "",
"status": status_el.get_text(strip=True) if status_el else "",
"score": score_el.get_text(strip=True) if score_el else "",
})
return {"matches": matches, "source": "espn_html"}

def match(match_id: str):
url = f"{BASE_URL}/match/{match_id}/commentary"
soup = _soup(url)

title_el = soup.select_one("h1.ds-text-tight-l")
title = title_el.get_text(strip=True) if title_el else "Unknown Match"

status_el = soup.select_one(".ds-text-tight-m.ds-font-regular")
status = status_el.get_text(strip=True) if status_el else "Status unavailable"

score_el = soup.select_one(".ds-text-compact-m.ds-text-typo")
score = score_el.get_text(strip=True) if score_el else "Score unavailable"

comm_list = [item.get_text(strip=True) for item in soup.select(".ds-text-tight-s.ds-font-regular")[:100]]

return {
"title": title,
"status": status,
"score": score,
"commentary": comm_list,
"source": "espn_html",
}
