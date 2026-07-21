"""Regression: installer/bootstrap must preserve diverged managed clones.

When ``~/.hermes/hermes-agent`` has local-only commits (or diverged history),
``git pull --ff-only`` fails with exit 128. Both installer scripts must stop
without resetting local commits to ``origin/$BRANCH``.

Fixes the bootstrap failure seen in #53257 and desktop update paths that run
``install.ps1`` / ``install.sh`` non-interactively.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = REPO_ROOT / "scripts" / "install.sh"
INSTALL_PS1 = REPO_ROOT / "scripts" / "install.ps1"


def _extract_install_sh_update_block() -> str:
    text = INSTALL_SH.read_text()
    match = re.search(
        r"(?P<block>git checkout \"\$BRANCH\".*?fi\n\n            if \[ -n \"\$autostash_ref\" \])",
        text,
        re.DOTALL,
    )
    assert match is not None, "managed-install update block not found in install.sh"
    return match["block"]


def _extract_install_ps1_branch_update_block() -> str:
    text = INSTALL_PS1.read_text()
    match = re.search(
        r"(?P<block>git -c windows\.appendAtomically=false checkout \$Branch.*?elseif \(\$Tag\))",
        text,
        re.DOTALL,
    )
    assert match is not None, "branch update block not found in install.ps1"
    return match["block"]


def test_install_sh_stops_without_reset_when_ff_only_pull_fails() -> None:
    block = _extract_install_sh_update_block()

    assert 'git pull --ff-only origin "$BRANCH"' in block
    assert 'git reset --hard "origin/$BRANCH"' not in block
    assert "Update refused" in block
    assert "Local commits and files were not reset" in block
    assert "exit 1" in block


def test_install_ps1_stops_without_reset_when_ff_only_pull_fails() -> None:
    block = _extract_install_ps1_branch_update_block()

    assert "pull --ff-only origin $Branch" in block
    assert 'reset --hard "origin/$Branch"' not in block
    assert "Update refused" in block
    assert "Local commits and files were not reset" in block
    assert "throw" in block
