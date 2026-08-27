import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

from collabx.core.models import EditorialBrief, PublishedNewsletter
from collabx.orchestration.collabx_engine import CollabXEngine

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

@app.post("/api/v1/editorial/produce-newsletter", response_model=PublishedNewsletter)
def produce_newsletter(brief: EditorialBrief):
    return engine.produce_edition(brief)
