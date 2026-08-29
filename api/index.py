"""Vercel serverless entrypoint.

Vercel's Python runtime imports this module and serves the ASGI application it
exports as `app`. It is a thin re-export on purpose: the deployment target must
not become a second definition of the service, or the hosted demo and the local
container drift apart without anyone noticing.

Everything else -- routes, static dashboard, provider selection -- comes from
`collabx.server`, exactly as it does under `uvicorn` and under Docker.

The hosted demo runs the deterministic engine. `vercel.json` pins
COLLABX_PROVIDER=deterministic so a public URL never holds an API key or spends
a free-tier quota that strangers and crawlers could drain.
"""
from collabx.server import app

__all__ = ["app"]
