# 📰 CollabX: Multi-Agent Editorial Team for High-Impact Newsletters & Reports

> **An orchestrated multi-agent framework coordinating specialized Researcher, Writer, and Editor agents in a collaborative state graph to produce publication-ready newsletters.**

> [!IMPORTANT]
> **Project status: reference scaffold, not a live agent system.**
> The domain models, pipeline wiring, HTTP gateway, dashboard, and deployment
> manifests are real and runnable. The three agents are **not** backed by an LLM —
> each returns fixed sample content, so every brief currently produces the same
> newsletter body regardless of topic, tone, or word-count target. Readability,
> tone, and fact-check scores are placeholder constants. See
> [Implemented vs. not yet implemented](#-implemented-vs-not-yet-implemented).

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![Tests Passing](https://img.shields.io/badge/Tests-17%20Passing-brightgreen.svg)]()
[![FastAPI](https://img.shields.io/badge/API-FastAPI%20%3A8014-teal.svg)](http://127.0.0.1:8014/docs)
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
3. **Single-Call Pipeline**: `POST /api/v1/editorial/produce-newsletter` runs
   Researcher → Writer → Editor and returns the complete edition in one response.
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
| Markdown → HTML compilation | ⚠️ Block-level only — no inline formatting (`**bold**` is not converted), no lists |
| LLM-backed research, writing, editing | ❌ Not implemented — agents return fixed sample content |
| Flesch-Kincaid readability scoring | ❌ Not implemented — `readability_score` is the constant `88.5` |
| Fact-check grounding against the dossier | ❌ Not implemented — `fact_check_passed` is always `True` |
| Tone alignment scoring | ❌ Not implemented — `tone_alignment_score` is the constant `0.94` |
| Editor → Writer revision loop | ❌ Not implemented — the engine is a straight line |
| Brief-driven output (`tone`, `target_word_count`) | ❌ Not implemented — only `topic` reaches the output, in the headline |

> `SPEC.md` describes the **target** design, including the revision loop and the
> quality gates. It is a specification to build against, not a description of
> current behaviour.

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

- **Interactive Editorial Studio**: [http://127.0.0.1:8014/](http://127.0.0.1:8014/)
- **Swagger OpenAPI Docs**: [http://127.0.0.1:8014/docs](http://127.0.0.1:8014/docs)

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
