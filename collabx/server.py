import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

from collabx.core.models import EditorialBrief, EditorialRequest, PublishedNewsletter
from collabx.orchestration.collabx_engine import CollabXEngine
from collabx.providers import provider_status

app = FastAPI(
    title="CollabX Multi-Agent Editorial Gateway",
    version="1.0.0",
    description="Orchestrated Team Agents (Researcher, Writer, Editor) for Publication-Grade Newsletters"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = CollabXEngine()

# Mount Static UI Files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_dashboard():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"service": "CollabX", "status": "active", "docs": "/docs"}

@app.get("/healthz")
def healthz():
    return {"status": "healthy", "service": "CollabX", "version": "1.0.0"}

@app.get("/readyz")
def readyz():
    return {"status": "ready", "editorial_team_agents_active": 3}

@app.get("/api/v1/providers")
def providers():
    """Which inference backend is active, and what else is configured.

    Exposed because "why is my output templated?" is the first question anyone
    hits, and the answer is always one of: no provider requested, no key set, or
    no local server running. Reports booleans and names only -- never a key.
    """
    return provider_status()


@app.post("/api/v1/editorial/produce-newsletter", response_model=PublishedNewsletter)
def produce_newsletter(request: EditorialRequest):
    """Produce an edition, optionally from research supplied with the request.

    `EditorialRequest` extends `EditorialBrief`, so a plain
    `{"topic": "..."}` body still works. Adding a `dossier` switches on the
    mode where the fact-check verifies claims against sources this system did
    not write.
    """
    brief = EditorialBrief(**request.model_dump(include=set(EditorialBrief.model_fields)))
    return engine.produce_edition(brief, supplied_dossier=request.dossier)
