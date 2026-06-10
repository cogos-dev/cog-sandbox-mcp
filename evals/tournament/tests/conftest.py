"""conftest.py for evals/tournament/tests.

Points COG_TOURNAMENT_ROOT at the committed fixture cogdocs when no external
workspace is configured. This makes the terminal-bench adapter tests pass in CI
(where ~/workspaces/cog does not exist) while preserving live-workspace loading
for developers who have the real tournament cogdoc tree.
"""

from __future__ import annotations

import os
from pathlib import Path

_FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures"


def pytest_configure(config) -> None:  # noqa: ANN001
    """Set COG_TOURNAMENT_ROOT to the in-repo fixtures unless already overridden.

    CI strategy: tournament tests run against the minimal cogdoc fixtures committed
    under evals/tournament/fixtures/. This means the tests genuinely exercise the
    adapter and scoring logic in CI rather than being skipped. Full cogdoc-coupled
    runs (against the live workspace tree) happen on dev machines where COGOS_WORKSPACE
    points at a real cog workspace. To opt into the live path locally, set
    COG_TOURNAMENT_ROOT explicitly before running pytest.
    """
    if "COG_TOURNAMENT_ROOT" not in os.environ:
        # Check whether the default workspace-derived path would actually work.
        # If not, fall back to the committed fixtures so CI stays green.
        workspace = os.environ.get(
            "COGOS_WORKSPACE",
            os.path.join(os.path.expanduser("~"), "workspaces", "cog"),
        )
        workspace_tournament = Path(
            workspace,
            ".cog",
            "mem",
            "semantic",
            "architecture",
            "tournament",
        )
        if not workspace_tournament.exists():
            os.environ["COG_TOURNAMENT_ROOT"] = str(_FIXTURE_ROOT)
