FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install -e .

# Free hosts each dictate their own port: Hugging Face Spaces requires 7860,
# Render and Fly inject $PORT. Honouring $PORT with a local default means the
# same image deploys anywhere without editing this file.
ENV PORT=8014

# The published demo must never hold a key or call a paid endpoint. The image
# defaults to the deterministic engine; a model is opted into at run time.
ENV COLLABX_PROVIDER=deterministic

EXPOSE 8014

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f "http://localhost:${PORT}/healthz" || exit 1

# Shell form so ${PORT} is expanded at container start, not baked in at build.
CMD uvicorn collabx.server:app --host 0.0.0.0 --port "${PORT}"
