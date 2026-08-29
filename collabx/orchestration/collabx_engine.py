"""The editorial desk: Researcher -> Writer -> Editor, with a revision loop.

The engine used to be a straight line. It now runs the Editor as a *gate*: if
the draft fails a quality gate, the Editor hands the Writer a `RevisionHint`
and composition runs again under tighter limits.

**Termination.** The loop is bounded by `max_revision_rounds`. A loop that can
send work backward without a hard bound is how a service hangs on one request,
and the Writer is a deterministic template engine -- if a round produces the
same text, further rounds cannot help either. The loop stops on any of three
conditions: all gates pass, the round budget is spent, or a round changed
nothing.

**Exhaustion.** When the budget runs out with gates still failing, the edition
is published anyway, carrying `revision_required=True` and a critique naming
every failing gate and its margin. The endpoint stays total; a caller that
wants to refuse a rejected draft checks the verdict.
"""
from collabx.agents.editor_agent import EditorAgent
from collabx.agents.researcher_agent import ResearcherAgent
from collabx.agents.writer_agent import RevisionHint, WriterAgent
from collabx.core.editorial_graph import EditorialGraph
from collabx.core.models import EditorialBrief, PublishedNewsletter
from collabx.core.tone import profile_for

# Two revisions past the first draft. Each round tightens the sentence limit;
# past three attempts a template writer has no further moves, so more rounds
# would burn time without changing the text.
DEFAULT_MAX_REVISION_ROUNDS = 2


class CollabXEngine:
    """
    CollabXEngine: Orchestrates the multi-agent editorial desk (Researcher -> Writer -> Editor).
    """

    def __init__(self, max_revision_rounds: int = DEFAULT_MAX_REVISION_ROUNDS):
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.editor = EditorAgent()
        self.max_revision_rounds = max(0, max_revision_rounds)

    def produce_edition(self, brief: EditorialBrief) -> PublishedNewsletter:
        # Step 1: Research
        dossier = self.researcher.conduct_research(brief)

        # Step 2: Write, then revise for as long as the Editor rejects the draft
        draft = self.writer.compose_draft(brief, dossier)
        rounds_used = 0

        for attempt in range(1, self.max_revision_rounds + 1):
            gates = EditorialGraph.gates_for(draft, brief, dossier)
            if all(gate.passed for gate in gates):
                break

            hint = self._hint_for(brief, attempt)
            revised = self.writer.compose_draft(brief, dossier, revision_hint=hint)

            if revised.raw_markdown == draft.raw_markdown:
                # The transforms had nothing left to change. Another round at
                # the same limits would produce the same text.
                break

            draft = revised
            rounds_used = attempt

        # Step 3: Edit & Publish. The verdict is honest whether or not the
        # gates ended up passing.
        return self.editor.review_and_publish(
            brief, draft, dossier, revision_rounds=rounds_used
        )

    @staticmethod
    def _hint_for(brief: EditorialBrief, attempt: int) -> RevisionHint:
        """Tighten the sentence limit with each round.

        Round 1 asks for the tone's own target. Later rounds go below it,
        because a draft that missed at the target needs more than the target.
        """
        profile = profile_for(brief.tone)
        max_words = max(8, profile.target_sentence_words - 2 * (attempt - 1))
        return RevisionHint(max_sentence_words=max_words, simplify_vocabulary=True)
