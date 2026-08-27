# 📰 CollabX: Multi-Agent Editorial Team for High-Impact Newsletters & Reports

> **An orchestrated multi-agent framework coordinating specialized Researcher, Writer, and Editor agents in a collaborative state graph to produce publication-ready newsletters.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![Tests Passing](https://img.shields.io/badge/Tests-200%2B%20Passing-brightgreen.svg)]()
[![FastAPI](https://img.shields.io/badge/API-FastAPI%20%3A8014-teal.svg)](http://127.0.0.1:8014/docs)
[![Author](https://img.shields.io/badge/Author-Asadullah%20Shafique-purple.svg)](https://asadullahshafique-devunity.vercel.app)

---

## 🚀 Key Value Propositions

1. **Specialized Multi-Agent Roles**:
   - **`ResearcherAgent`**: Uncovers breaking industry signals, primary statistics, and executive quotes.
   - **`WriterAgent`**: Crafts compelling narrative arcs, catchy hooks, and structured body sections.
   - **`EditorAgent`**: Enforces strict readability benchmarks (Flesch-Kincaid $\ge 80$), verifies facts, and refines tone.
2. **Collaborative State-Graph Pipeline**: Automatically passes context between agents with built-in revision loops to ensure publication-ready output.
3. **Dual Markdown & HTML Output**: Produces clean markdown for CMS platforms and responsive HTML for email newsletter broadcasts.
4. **Zero-Hallucination Fact-Checking**: Ensures all claims and statistics in the writer's draft map back to the researcher's verified dossier.
5. **Interactive Editorial Studio**: Glassmorphic bilingual (English/Arabic RTL) dashboard with live pipeline progress, multi-agent workspace, and full newsletter reader.

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

# 2. Install dependencies
pip install -e .

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
