import time
from typing import Any, Dict

from cache import cache
from providers import cricbuzz_json as cbj
from providers import cricbuzz_html as cbh
from providers import espn_html as espn

class CricketAPIError(Exception):
pass

MAX_RETRIES = 3
BACKOFF = 1.5

def _with_retries(fn, *args, **kwargs):
last_exc=None
for attempt in range(1, MAX_RETRIES+1):
try:
return fn(*args, **kwargs)
except Exception as e:
last_exc=e
if attempt==MAX_RETRIES:
break
time.sleep(BACKOFF*attempt)
raise CricketAPIError(str(last_exc))

def _cached(key, ttl, fn, *args):
cached = cache.get(key)
if cached is not None:
return cached
data = _with_retries(fn, *args)
cache.set(key, data, ttl)
return data

def _fallback_chain(key, ttl, json_fn, html_fn, espn_fn, *args):
try: return _cached(f"{key}:cb_json", ttl, json_fn, *args)
except: pass
try: return _cached(f"{key}:cb_html", ttl, html_fn, *args)
except: pass
try: return _cached(f"{key}:espn_html", ttl, espn_fn, *args)
except Exception as e:
raise CricketAPIError(f"All providers failed: {e}")

def get_live_matches():
return _fallback_chain("live", 5, cbj.live_matches, cbh.live_matches, espn.live_matches)

def get_recent_matches():
try: return _cached("recent:cb_json", 30, cbj.recent_matches)
except: return _cached("recent:cb_html", 30, cbh.live_matches)

def get_upcoming_matches():
try: return _cached("upcoming:cb_json", 60, cbj.upcoming_matches)
except: return _cached("upcoming:cb_html", 60, cbh.live_matches)

def get_match(match_id):
return _fallback_chain(f"match:{match_id}", 5, cbj.match, cbh.match, espn.match, match_id)

def get_scorecard(match_id):
try: return _cached(f"score:{match_id}:cb_json", 5, cbj.scorecard, match_id)
except: return get_match(match_id)

def get_commentary(match_id):
try: return _cached(f"comm:{match_id}:cb_json", 3, cbj.commentary, match_id)
except: return get_match(match_id)

def get_timeline(match_id):
try: return _cached(f"timeline:{match_id}:cb_json", 5, cbj.timeline, match_id)
except: return get_match(match_id)

def get_stats(match_id):
try: return _cached(f"stats:{match_id}:cb_json", 30, cbj.stats, match_id)
except: return get_match(match_id)

def filter_matches_by_team(matches_json, team_name):
team_name = team_name.lower()
filtered=[]
for match in matches_json.get("matches", []):
teams=[]
if isinstance(match, dict):
t1 = match.get("team1") or match.get("team1_name") or {}
t2 = match.get("team2") or match.get("team2_name") or {}
if isinstance(t1, dict): teams.append(t1.get("name","") or t1.get("sName",""))
else: teams.append(str(t1))
if isinstance(t2, dict): teams.append(t2.get("name","") or t2.get("sName",""))
else: teams.append(str(t2))
if any(team_name in (t or "").lower() for t in teams):
filtered.append(match)
return filtered
