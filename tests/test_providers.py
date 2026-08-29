"""Provider selection, fallback, and the promise that a missing model never
turns into a failed request.

Nothing here touches the network. Providers are exercised through injected
fakes, because a test that needs a running Ollama server or a live API key is
a test that fails in CI for reasons unrelated to the code.
"""
import pytest

from collabx.agents.researcher_agent import UNVERIFIED_SOURCE, ResearcherAgent
from collabx.agents.writer_agent import WriterAgent
from collabx.core.models import DossierProvenance, EditorialBrief
from collabx.providers import PROVIDERS, provider_status, resolve_provider
from collabx.providers.base import ProviderUnavailable
from collabx.providers.deterministic import DeterministicProvider, is_model_backed
from collabx.providers.gemini import GeminiProvider
from collabx.providers.ollama import OllamaProvider


class FakeProvider:
    """A model that returns whatever the test hands it."""

    name = "fake"

    def __init__(self, response="", fail=False):
        self.response = response
        self.fail = fail
        self.prompts = []

    def available(self) -> bool:
        return True

    def complete(self, prompt, *, max_tokens=1024, temperature=0.2):
        self.prompts.append(prompt)
        if self.fail:
            raise ProviderUnavailable("simulated outage")
        return self.response


# --- selection -------------------------------------------------------------


@pytest.mark.parametrize("value", [None, "", "auto", "AUTO", "deterministic"])
def test_default_selection_is_deterministic(monkeypatch, value):
    # A fresh clone must behave identically everywhere. Opting in to a model is
    # explicit, so `auto` must not pick up a stray local server.
    if value is None:
        monkeypatch.delenv("COLLABX_PROVIDER", raising=False)
    else:
        monkeypatch.setenv("COLLABX_PROVIDER", value)
    assert resolve_provider().name == "deterministic"


def test_unknown_provider_name_falls_back_rather_than_raising(monkeypatch):
    monkeypatch.setenv("COLLABX_PROVIDER", "not-a-real-provider")
    assert resolve_provider().name == "deterministic"


def test_gemini_without_a_key_falls_back(monkeypatch):
    monkeypatch.setenv("COLLABX_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert resolve_provider().name == "deterministic"


def test_a_provider_whose_probe_explodes_still_falls_back(monkeypatch):
    class Exploding:
        name = "exploding"

        def available(self):
            raise RuntimeError("probe blew up")

    monkeypatch.setitem(PROVIDERS, "exploding", Exploding)
    monkeypatch.setenv("COLLABX_PROVIDER", "exploding")
    # An availability probe must never be able to fail a request.
    assert resolve_provider().name == "deterministic"


def test_is_model_backed_distinguishes_the_null_provider():
    assert is_model_backed(FakeProvider()) is True
    assert is_model_backed(DeterministicProvider()) is False


# --- the null provider -----------------------------------------------------


def test_deterministic_provider_is_always_available():
    assert DeterministicProvider().available() is True


def test_deterministic_provider_refuses_to_complete():
    with pytest.raises(ProviderUnavailable):
        DeterministicProvider().complete("anything")


# --- configuration ---------------------------------------------------------


def test_gemini_availability_is_key_presence_only(monkeypatch):
    # Must not spend a quota unit or a round trip just to answer "am I usable".
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    assert GeminiProvider().available() is True
    monkeypatch.delenv("GEMINI_API_KEY")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert GeminiProvider().available() is False


def test_gemini_reads_model_from_the_environment(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-pinned-1.0")
    assert GeminiProvider().model == "gemini-pinned-1.0"


def test_ollama_reads_host_and_model_from_the_environment(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "http://example.invalid:1234/")
    monkeypatch.setenv("OLLAMA_MODEL", "some-model")
    provider = OllamaProvider()
    assert provider.host == "http://example.invalid:1234"  # trailing slash trimmed
    assert provider.model == "some-model"


def test_ollama_is_unavailable_when_no_server_is_listening(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:1")
    assert OllamaProvider().available() is False


def test_provider_status_never_reveals_a_key(monkeypatch):
    secret = "AIza-this-must-never-appear-anywhere"
    monkeypatch.setenv("GEMINI_API_KEY", secret)
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:1")
    status = provider_status()
    assert "gemini" in status["available"]
    assert secret not in repr(status)


# --- agents fall back rather than fail -------------------------------------


def test_writer_falls_back_to_template_when_the_model_fails():
    brief = EditorialBrief(topic="Enterprise AI")
    dossier = ResearcherAgent(provider=DeterministicProvider()).conduct_research(brief)
    draft = WriterAgent(provider=FakeProvider(fail=True)).compose_draft(brief, dossier)
    # A missing model degrades quality, never availability.
    assert draft.raw_markdown.strip()
    assert draft.sections


def test_writer_falls_back_when_the_model_returns_unusable_output():
    brief = EditorialBrief(topic="Enterprise AI")
    dossier = ResearcherAgent(provider=DeterministicProvider()).conduct_research(brief)
    # No '## ' headings: not a newsletter, so it must not be published as one.
    draft = WriterAgent(provider=FakeProvider(response="just a sentence")).compose_draft(
        brief, dossier
    )
    assert len(draft.sections) > 1


def test_writer_uses_model_output_when_it_is_usable():
    brief = EditorialBrief(topic="Enterprise AI")
    dossier = ResearcherAgent(provider=DeterministicProvider()).conduct_research(brief)
    body = "A hook line.\n\n## First Section\n\nSome body text.\n\n## What This Means\n\nA close."
    draft = WriterAgent(provider=FakeProvider(response=body)).compose_draft(brief, dossier)
    assert [s.heading for s in draft.sections] == ["First Section", "What This Means"]
    assert "Some body text." in draft.raw_markdown


def test_the_editors_critique_is_passed_back_to_the_model():
    # This is what makes the loop a critique-and-revise cycle rather than a retry.
    from collabx.agents.writer_agent import RevisionHint

    brief = EditorialBrief(topic="Enterprise AI")
    dossier = ResearcherAgent(provider=DeterministicProvider()).conduct_research(brief)
    fake = FakeProvider(response="Hook.\n\n## S\n\nBody.")
    WriterAgent(provider=fake).compose_draft(
        brief,
        dossier,
        revision_hint=RevisionHint(12, True, critique=["Readability is 20.0 against a 40 floor."]),
    )
    assert "Readability is 20.0 against a 40 floor." in fake.prompts[-1]


# --- researcher provenance -------------------------------------------------


def test_researcher_returns_the_fixture_without_a_model():
    dossier = ResearcherAgent(provider=DeterministicProvider()).conduct_research(
        EditorialBrief(topic="Anything")
    )
    assert dossier.provenance is DossierProvenance.FIXTURE
    assert dossier.is_verifiable is False


def test_model_generated_research_is_labelled_and_never_carries_a_real_url():
    # An invented citation that looks real is the worst output this system
    # could produce: it survives a glance and fails an audit.
    response = """[
      {"headline": "Prices moved", "statistic": "Prices moved 12% in Q3.",
       "quote": "It was a volatile quarter.",
       "source_url": "https://reuters.com/totally-real-article"}
    ]"""
    dossier = ResearcherAgent(provider=FakeProvider(response=response)).conduct_research(
        EditorialBrief(topic="Dairy Pricing")
    )
    assert dossier.provenance is DossierProvenance.MODEL_GENERATED
    assert dossier.is_verifiable is False
    assert dossier.findings[0].source_url == UNVERIFIED_SOURCE
    assert "reuters.com" not in dossier.findings[0].source_url


def test_model_research_survives_a_fenced_json_response():
    response = '```json\n[{"headline": "H", "statistic": "Up 4%.", "quote": "Q"}]\n```'
    dossier = ResearcherAgent(provider=FakeProvider(response=response)).conduct_research(
        EditorialBrief(topic="X")
    )
    assert dossier.provenance is DossierProvenance.MODEL_GENERATED
    assert len(dossier.findings) == 1


def test_unparseable_model_research_falls_back_to_the_fixture():
    dossier = ResearcherAgent(provider=FakeProvider(response="I cannot help with that.")).conduct_research(
        EditorialBrief(topic="X")
    )
    assert dossier.provenance is DossierProvenance.FIXTURE
