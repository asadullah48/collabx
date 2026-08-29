# Deploying CollabX

The image honours `$PORT` and defaults to the deterministic engine, so it
deploys to any free host without edits and without a key.

**The published demo deliberately does not call a model.** A public URL wired
to a personal free-tier key is one crawler away from an exhausted quota, and a
demo link that returns 500 is worse than no demo link. The hosted build runs
the deterministic engine, which behaves identically for every visitor, forever.

---

## Vercel — currently live at <https://collabx-gamma.vercel.app>

`vercel.json` and `api/index.py` are committed, so Vercel needs no
configuration. It detects the Python builder, installs `requirements.txt`, and
serves `collabx.server:app` through `api/index.py`.

Redeploy from the CLI:

```bash
vercel deploy --prod --yes
```

Or from the dashboard: <https://vercel.com/new> → **Import Git Repository** →
`asadullah48/collabx` → framework preset **Other** → **Deploy**.

> [!WARNING]
> Use the **production alias** Vercel assigns. A hand-created alias
> (`vercel alias set ...`) lands behind Vercel SSO and redirects visitors to a
> login page — verified during setup, and fatal for a public demo. Always
> confirm a URL is reachable while signed out:
>
> ```bash
> curl -s -o /dev/null -w '%{http_code}\n' https://<url>/healthz   # want 200, not 302
> ```

No environment variables are needed. The demo runs the deterministic engine
because `vercel.json` pins `COLLABX_PROVIDER=deterministic`, so the public URL
holds no key and cannot exhaust anyone's quota.

Once it is live, publish the link on the repository itself so it shows in the
GitHub sidebar:

```bash
gh repo edit asadullah48/collabx --homepage "https://<your-deployment>.vercel.app"
```

Verify the deployment:

```bash
curl -s https://<your-deployment>.vercel.app/healthz
curl -s https://<your-deployment>.vercel.app/api/v1/providers
```

`/api/v1/providers` should report `"active": "deterministic"` and
`"llm_backed": false`. If it reports anything else, a stray environment
variable is set on the project.

---

## Hugging Face Spaces (free, recommended)

Spaces is where people go looking for AI projects, and the Docker SDK runs this
image unmodified.

1. Create a Space: **SDK = Docker**, hardware = **CPU basic (free)**.
2. Push this repository to the Space remote.
3. Add this front matter to the top of the `README.md` **in the Space repo**
   (Spaces reads its configuration from there):

```yaml
---
title: CollabX Editorial Desk
emoji: 📰
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
---
```

4. Set the Space variable `PORT=7860`, or rely on `app_port` above.

Leave `COLLABX_PROVIDER` unset. The image already defaults to `deterministic`.

---

## Render (free web service)

1. New → Web Service → connect the repository.
2. Runtime **Docker**. Render injects `$PORT`, which the image already honours.
3. Health check path: `/healthz`.

No environment variables are required.

---

## Fly.io

```bash
fly launch --no-deploy      # generates fly.toml
fly deploy
```

Set `internal_port` in `fly.toml` to match `$PORT` (default 8014).

---

## Running it yourself with a model

Hosting stays deterministic; local runs do not have to be.

```bash
# free, local, offline, no key
ollama pull llama3.2
COLLABX_PROVIDER=ollama uvicorn collabx.server:app --port 8014

# free tier, needs a key from https://aistudio.google.com/apikey
COLLABX_PROVIDER=gemini GEMINI_API_KEY=... uvicorn collabx.server:app --port 8014
```

Confirm which engine is live:

```bash
curl -s localhost:8014/api/v1/providers
```

That endpoint reports names and booleans only. It never echoes a key.

---

## Docker locally

```bash
docker build -t collabx .
docker run -p 8014:8014 collabx

# with a model, passing the key at run time rather than baking it into the image
docker run -p 8014:8014 -e COLLABX_PROVIDER=gemini -e GEMINI_API_KEY=... collabx
```

Never `COPY` a `.env` into the image. `.dockerignore` excludes it; keep it that way.

---

## Kubernetes

The chart in `helm/` wires liveness and readiness probes to `/healthz` and
`/readyz`. Set `PORT` in `values.yaml` if your ingress expects something other
than 8014.
