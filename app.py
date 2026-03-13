from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

import core_client as core
from core_client import CricketAPIError

app = FastAPI(
    title="Cricket Score API",
    version="1.0.0",
    description="Cricbuzz JSON + Cricbuzz HTML + ESPN HTML with caching, retries, and fallbacks."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Cricket Score API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/live")
def live_matches(team: Optional[str] = Query(default=None, description="Filter by team name")):
    try:
        data = core.get_live_matches()
        if team:
            data = {
                "matches": core.filter_matches_by_team(data, team),
                "source": data.get("source")
            }
        return data
    except CricketAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/matches/recent")
def recent_matches(team: Optional[str] = None):
    try:
        data = core.get_recent_matches()
        if team:
            data = {
                "matches": core.filter_matches_by_team(data, team),
                "source": data.get("source")
            }
        return data
    except CricketAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/matches/upcoming")
def upcoming_matches(team: Optional[str] = None):
    try:
        data = core.get_upcoming_matches()
        if team:
            data = {
                "matches": core.filter_matches_by_team(data, team),
                "source": data.get("source")
            }
        return data
    except CricketAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/match/{match_id}")
def match_info(match_id: str):
    try:
        return core.get_match(match_id)
    except CricketAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/match/{match_id}/scorecard")
def match_scorecard(match_id: str):
    try:
        return core.get_scorecard(match_id)
    except CricketAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/match/{match_id}/commentary")
def match_commentary(match_id: str):
    try:
        return core.get_commentary(match_id)
    except CricketAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/match/{match_id}/commentary/historical")
def match_commentary_historical(match_id: str):
    try:
        return core.get_commentary(match_id)
    except CricketAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/match/{match_id}/timeline")
def match_timeline(match_id: str):
    try:
        return core.get_timeline(match_id)
    except CricketAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/match/{match_id}/stats")
def match_stats(match_id: str):
    try:
        return core.get_stats(match_id)
    except CricketAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


# ---------- DEBUG ENDPOINTS ----------

@app.get("/debug/live-providers")
def debug_live_providers():
    from providers import cricbuzz_json as cbj
    from providers import cricbuzz_html as cbh
    from providers import espn_html as espn

    out = {}

    try:
        out["cb_json"] = cbj.live_matches()
    except Exception as e:
        out["cb_json_error"] = str(e)

    try:
        out["cb_html"] = cbh.live_matches()
    except Exception as e:
        out["cb_html_error"] = str(e)

    try:
        out["espn_html"] = espn.live_matches()
    except Exception as e:
        out["espn_html_error"] = str(e)

    return out
