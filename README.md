# 📰 CollabX: Multi-Agent Editorial Team for High-Impact Newsletters & Reports

> **An orchestrated multi-agent framework coordinating specialized Researcher, Writer, and Editor agents in a collaborative state graph to produce publication-ready newsletters.**

**The interesting part is not that it calls a model. It is that it does not trust one.**

CollabX scores every draft it produces: real Flesch Reading Ease against a
per-tone floor, every statistic and quotation traced back to a source dossier,
and a bounded Editor → Writer revision loop that sends failing drafts back with
the specific critique that failed them. Those gates run identically whether the
prose came from a language model or from the built-in template engine.

> [!IMPORTANT]
> **It runs with no API key, no model, and no network.** That is the default.
> `git clone`, `pip install -e .`, `uvicorn` — and it works. A model is an
> opt-in upgrade ([free options below](#-running-it-with-a-model-free)), never a
> requirement, because a project you cannot run is a screenshot.

<!-- The CI badge is live: it reflects the actual result of the most recent run
     on main, across Python 3.10-3.13 on Linux and Windows. It is not a static
     image asserting a number that nothing checks. -->
[![CI](https://github.com/asadullah48/collabx/actions/workflows/ci.yml/badge.svg)](https://github.com/asadullah48/collabx/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![No API key required](https://img.shields.io/badge/API%20key-not%20required-brightgreen.svg)](#-running-it-with-a-model-free)
[![Author](https://img.shields.io/badge/Author-Asadullah%20Shafique-purple.svg)](https://asadullahshafique-devunity.vercel.app)

---

## 🚀 What CollabX Provides

1. **Specialized Multi-Agent Roles** — three separable stages with distinct
   responsibilities and a typed hand-off between each:
   - **`ResearcherAgent`**: produces a `ResearchDossier` of findings and core themes.
   - **`WriterAgent`**: produces an `ArticleDraft` — headline, hook, and structured sections.
   - **`EditorAgent`**: produces a `PublishedNewsletter` with feedback and compiled HTML.
2. **Typed Editorial Domain Model**: eight Pydantic models (`EditorialBrief`,
   `ResearchDossier`, `ArticleDraft`, `EditorFeedback`, `PublishedNewsletter`, …)
   that define the contract between stages and the shape of the API response.
3. **Single-Call Pipeline with a Revision Loop**:
   `POST /api/v1/editorial/produce-newsletter` runs Researcher → Writer → Editor
   and returns the complete edition in one response. The Editor acts as a gate:
   a draft that misses its readability, grounding, or tone gate is sent back to
   the Writer under tighter limits. The loop is bounded and stops when the gates
   pass, the budget is spent, or a round changes nothing.
   **The endpoint is total.** If the budget runs out with gates still failing,
   the edition is still returned, carrying `revision_required: true` and a
   critique naming each failing gate and its margin.
4. **Deterministic Output**: identical briefs produce identical editions and
   identical IDs across processes, which makes the pipeline straightforward to test.
5. **Interactive Editorial Studio**: glassmorphic bilingual (English/Arabic RTL)
   dashboard that submits a brief and renders the returned edition, research
   signals, and the editor's critique notes.
6. **Deployment Manifests**: Dockerfile, Compose service, and a Helm chart with
   liveness/readiness probes wired to `/healthz` and `/readyz`.

---

## 🧭 Implemented vs. Not Yet Implemented

| Capability | Status |
| :--- | :--- |
| Typed models & stage hand-off | ✅ Implemented |
| FastAPI gateway, health probes, static dashboard | ✅ Implemented |
| Docker / Compose / Helm packaging | ✅ Implemented |
| Deterministic, reproducible edition IDs | ✅ Implemented |
| HTML escaping in `html_body` | ✅ Implemented — text nodes are escaped, so a topic carrying markup cannot become live HTML |
| Flesch Reading Ease scoring | ✅ Implemented — computed from the draft in `core/readability.py` |
| Fact-check grounding against the dossier | ✅ Implemented — statistics and quotations only, see the caveat below |
| Tone alignment scoring | ✅ Implemented — sentence length and long-word density against a per-tone profile |
| Editor → Writer revision loop | ✅ Implemented — bounded, and reports how many rounds it used |
| Brief-driven output (`tone`, `target_word_count`) | ✅ Implemented — tone drives headline, hook, register and the readability floor; word count drives elaboration depth |
| Topic-drift detection | ✅ Implemented — warns when the dossier shares no vocabulary with the brief topic |
| Markdown → HTML compilation | ⚠️ Block-level only — no inline formatting (`**bold**` is not converted), no lists |
| Fact-check coverage | ⚠️ Statistics and quotations only. A confidently wrong *prose* sentence passes: verifying it needs semantic matching, not string comparison |
| Word-count target | ⚠️ Reported, never gated. The Writer composes from the dossier and will not pad to hit a number |
| Pluggable model providers | ✅ Implemented — Ollama (local, free), Gemini (free tier), or none. Zero vendor SDKs: every provider is plain HTTP via the standard library |
| Caller-supplied research | ✅ Implemented — POST your own dossier and the fact-check verifies against sources this system did not write |
| Source provenance labelling | ✅ Implemented — every response says whether research was `CALLER_SUPPLIED`, `MODEL_GENERATED`, or the built-in `FIXTURE` |
| Automatic web research | ❌ Not implemented — a model cannot browse. Model-drafted findings are labelled unverified and are **never** given fabricated source URLs |

### What the scores do and do not mean

- **`readability_score`** is a real Flesch Reading Ease value. The gate is **per
  tone**, not global. A single 80.0 threshold was unreachable: FRE 80–89 is
  6th-grade reading level, while this newsletter's stated audience is "CTOs,
  Founders & Enterprise Architects", which is the 30–59 band.
- **`fact_check_passed`** means *no unsupported statistic or quotation was
  found*. A draft containing no figures and no quotations has nothing to check,
  and the critique notes say so explicitly rather than implying verification
  happened.
- **`tone_alignment_score`** is two structural proxies, not a judgement of
  voice. A draft can score 1.00 and still sound wrong.
- **Provenance decides what any of it is worth.** The Editor verifies the
  Writer against the dossier, so the fact-check is only as good as the research
  behind it. Against a model-generated dossier, `fact_check_passed: true` means
  the Writer copied the Researcher faithfully — nothing about the world. Every
  response says which case it is, in plain language.

---

## 🔌 Running it with a model (free)

Three ways, none of which cost anything:

| | Setup | Key | Cost |
| :--- | :--- | :--- | :--- |
| **Deterministic** (default) | nothing | none | free |
| **Ollama** | `ollama pull llama3.2` | none | free, local, offline |
| **Gemini** | [free key](https://aistudio.google.com/apikey) | `GEMINI_API_KEY` | free tier |

```bash
COLLABX_PROVIDER=ollama uvicorn collabx.server:app --port 8014
COLLABX_PROVIDER=gemini uvicorn collabx.server:app --port 8014

curl -s localhost:8014/api/v1/providers   # which engine is live (never echoes a key)
```

If a provider is unreachable, out of quota, or returns something unusable, the
request **falls back to the deterministic engine and still succeeds**. A missing
model degrades the quality of the output, never the availability of the service.

### Making the fact-check mean something

Post your own research and the gate verifies against sources CollabX did not
write. This is the mode the project is actually for:

```bash
curl -X POST localhost:8014/api/v1/editorial/produce-newsletter \
  -H 'Content-Type: application/json' -d '{
    "topic": "Regional Dairy Pricing Volatility",
    "dossier": {
      "dossier_id": "D1",
      "topic": "Regional Dairy Pricing Volatility",
      "findings": [{
        "headline": "Farmgate prices swung sharply in Q3",
        "statistic": "Farmgate milk prices moved 12% between July and September.",
        "source_url": "https://example.gov/dairy/q3-report",
        "verified_quote": "Processors absorbed most of the volatility."
      }],
      "core_themes": ["Dairy pricing volatility"]
    }
  }'
```

> `SPEC.md` describes the **target** design. The revision loop and quality gates
> it specifies are now built; LLM-backed agents are not.

---

## 🏛️ CollabX Architecture

```
                    ┌─────────────────────────┐
                    │     Editorial Brief     │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     ResearcherAgent     │
                    │  • Statistics & Quotes  │
                    │  • Core Themes          │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │       WriterAgent       │
                    │  • Catchy Hooks         │
                    │  • Long-Form Narrative  │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │       EditorAgent       │
                    │  • Readability Scoring  │
                    │  • HTML Compilation     │
                    └─────────────────────────┘
```

---

## 🛠️ Quick Start

```powershell
# 1. Clone repository
git clone https://github.com/asadullah48/collabx.git
cd collabx

# 2. Install the package plus test dependencies
pip install -e ".[dev]"

# 3. Run automated test suite
python -m pytest tests -v

# 4. Start local gateway & frontend editorial studio
uvicorn collabx.server:app --host 127.0.0.1 --port 8014 --reload
```

No API key, no model download, no configuration. Step 4 serves a working
editorial desk.

- **Interactive Editorial Studio**: [http://127.0.0.1:8014/](http://127.0.0.1:8014/)
- **Swagger OpenAPI Docs**: [http://127.0.0.1:8014/docs](http://127.0.0.1:8014/docs)
- **Active provider**: [http://127.0.0.1:8014/api/v1/providers](http://127.0.0.1:8014/api/v1/providers)

Deployment to free hosting (Hugging Face Spaces, Render, Fly) is documented in
[DEPLOY.md](DEPLOY.md).

---

## 🧪 How this is verified

Claims in this README are checked, because an earlier version of this project
carried a "200+ tests" badge over a suite of 10 tautological ones.

- **152 tests**, run by [CI](.github/workflows/ci.yml) on Python 3.10–3.13,
  Linux and Windows.
- **The wheel is installed to a clean prefix and run from outside the source
  tree** on every CI run. The suite passes whether or not packaging works,
  because pytest imports from the working directory — this repository has
  already shipped a build that was broken while every test passed.
- **The API is booted and hit with real HTTP requests** in CI, not just
  TestClient.
- **Every quality feature is mutation-tested.** Reverting readability scoring,
  grounding, tone scoring, the per-tone floors, the revision loop, HTML
  escaping, or span protection each turns tests red. A test that still passes
  with the feature removed is decoration.
- **CI never calls a model** (`COLLABX_PROVIDER=deterministic`), so runs are
  hermetic: no key, no network, no flake.

---

## 🌐 Connected Ecosystem & Portfolio

- **DevUnity Portfolio**: [https://asadullahshafique-devunity.vercel.app](https://asadullahshafique-devunity.vercel.app)
- **DocuCode**: [https://github.com/asadullah48/docucode](https://github.com/asadullah48/docucode)
- **PrivateBrain**: [https://github.com/asadullah48/privatebrain](https://github.com/asadullah48/privatebrain)
- **ResearchX**: [https://github.com/asadullah48/researchx](https://github.com/asadullah48/researchx)
- **GraphAI**: [https://github.com/asadullah48/graphai](https://github.com/asadullah48/graphai)
- **LoopAI**: [https://github.com/asadullah48/loopai](https://github.com/asadullah48/loopai)
- **HarnessAI**: [https://github.com/asadullah48/harnessai](https://github.com/asadullah48/harnessai)
- **SecureBridge**: [https://github.com/asadullah48/securebridge](https://github.com/asadullah48/securebridge)
- **WorkforceAI Academy**: [https://github.com/asadullah48/workforceai-academy](https://github.com/asadullah48/workforceai-academy)
- **ConciergeAgent**: [https://github.com/asadullah48/conciergeagent](https://github.com/asadullah48/conciergeagent)
- **ContextX**: [https://github.com/asadullah48/contextx](https://github.com/asadullah48/contextx)
- **GuardrailAI**: [https://github.com/asadullah48/guardrailai](https://github.com/asadullah48/guardrailai)
- **MarketAgentHub**: [https://github.com/asadullah48/marketagenthub](https://github.com/asadullah48/marketagenthub)
- **WorkforceAI**: [https://github.com/asadullah48/workforceai](https://github.com/asadullah48/workforceai)
- **DomainX**: [https://github.com/asadullah48/domainx](https://github.com/asadullah48/domainx)
