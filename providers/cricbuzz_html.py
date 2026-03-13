"""
Cricbuzz HTML scraping has been disabled because Cricbuzz switched to a
React/Next.js client-rendered frontend. The HTML returned to servers
contains no match data, so scraping is no longer possible.

This provider remains as a stub so the fallback chain stays intact.
"""

from typing import Dict, Any


def live_matches() -> Dict[str, Any]:
    return {
        "matches": [],
        "source": "cricbuzz_html_disabled",
        "note": "Cricbuzz HTML no longer contains match data (React-rendered)."
    }


def recent_matches() -> Dict[str, Any]:
    return {
        "matches": [],
        "source": "cricbuzz_html_disabled",
        "note": "Cricbuzz HTML no longer contains match data (React-rendered)."
    }


def upcoming_matches() -> Dict[str, Any]:
    return {
        "matches": [],
        "source": "cricbuzz_html_disabled",
        "note": "Cricbuzz HTML no longer contains match data (React-rendered)."
    }


def match(match_id: str) -> Dict[str, Any]:
    return {
        "error": "HTML scraping disabled — use Cricbuzz JSON instead.",
        "source": "cricbuzz_html_disabled",
        "match_id": match_id
    }
