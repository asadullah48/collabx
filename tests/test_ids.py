import os
import subprocess
import sys

from collabx.core.ids import stable_suffix


def test_stable_suffix_is_deterministic_and_bounded():
    assert stable_suffix("Enterprise AI", 10000) == stable_suffix("Enterprise AI", 10000)
    assert 0 <= stable_suffix("Enterprise AI", 10000) < 10000


def test_stable_suffix_varies_by_topic():
    assert stable_suffix("Topic A", 10000) != stable_suffix("Topic B", 10000)


def test_editorial_ids_survive_hash_randomization():
    """IDs must not change between processes with different PYTHONHASHSEED values."""
    script = (
        "from collabx.orchestration.collabx_engine import CollabXEngine;"
        "from collabx.core.models import EditorialBrief;"
        "p = CollabXEngine().produce_edition(EditorialBrief(topic='Fixed Topic'));"
        "print(p.research_dossier.dossier_id, p.edition_id)"
    )
    outputs = []
    for seed in ("1", "2", "3"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, env=env, check=True,
        )
        outputs.append(result.stdout.strip())

    assert len(set(outputs)) == 1, f"IDs varied across hash seeds: {outputs}"
