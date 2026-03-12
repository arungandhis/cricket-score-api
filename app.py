from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

import core_client as core
from core_client import CricketAPIError

app = FastAPI(
title="Cricket Score API",
version="1.0.0",
description="Cricbuzz JSON + Cricbuzz HTML + ESPN HTML with caching and retries."
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
def live(team: Optional[str] = None):
try:
data = core.get_live_matches()
if team:
data = {"matches": core.filter_matches_by_team(data, team), "source": data.get("source")}
return data
except CricketAPIError as e:
raise HTTPException(502, str(e))

@app.get("/matches/recent")
def recent(team: Optional[str] = None):
try:
data = core.get_recent_matches()
if team:
data = {"matches": core.filter_matches_by_team(data, team), "source": data.get("source")}
return data
except CricketAPIError as e:
raise HTTPException(502, str(e))

@app.get("/matches/upcoming")
def upcoming(team: Optional[str] = None):
try:
data = core.get_upcoming_matches()
if team:
data = {"matches": core.filter_matches_by_team(data, team), "source": data.get("source")}
return data
except CricketAPIError as e:
raise HTTPException(502, str(e))

@app.get("/match/{match_id}")
def match(match_id: str):
try:
return core.get_match(match_id)
except CricketAPIError as e:
raise HTTPException(502, str(e))

@app.get("/match/{match_id}/scorecard")
def scorecard(match_id: str):
try:
return core.get_scorecard(match_id)
except CricketAPIError as e:
raise HTTPException(502, str(e))

@app.get("/match/{match_id}/commentary")
def commentary(match_id: str):
try:
return core.get_commentary(match_id)
except CricketAPIError as e:
raise HTTPException(502, str(e))

@app.get("/match/{match_id}/commentary/historical")
def commentary_historical(match_id: str):
try:
return core.get_commentary(match_id)
except CricketAPIError as e:
raise HTTPException(502, str(e))

@app.get("/match/{match_id}/timeline")
def timeline(match_id: str):
try:
return core.get_timeline(match_id)
except CricketAPIError as e:
raise HTTPException(502, str(e))

@app.get("/match/{match_id}/stats")
def stats(match_id: str):
try:
return core.get_stats(match_id)
except CricketAPIError as e:
raise HTTPException(502, str(e))
