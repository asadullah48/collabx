# 📰 CollabX: Multi-Agent Editorial Team for High-Impact Newsletters & Reports

> **An orchestrated multi-agent framework coordinating specialized Researcher, Writer, and Editor agents in a collaborative state graph to produce publication-ready newsletters.**

> [!IMPORTANT]
> **Project status: a working deterministic editorial engine, not an LLM agent system.**
> The quality gates are real. Readability is a computed Flesch Reading Ease score,
> fact-checking traces every statistic and quotation back to the research dossier,
> and a bounded Editor → Writer revision loop rewrites drafts that miss their
> gates. The **Researcher is still a fixture** — it returns the same two findings
> for any topic — and the **Writer is a template engine, not a language model**.
> Wiring the agents to a model is the remaining work. See
> [Implemented vs. not yet implemented](#-implemented-vs-not-yet-implemented).

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![Tests Passing](https://img.shields.io/badge/Tests-128%20Passing-brightgreen.svg)]()
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
| LLM-backed research and writing | ❌ Not implemented — the Researcher returns the same two findings for any topic, and the Writer is a template engine |

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
