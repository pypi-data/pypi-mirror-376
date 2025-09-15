"""Meta-test for CLI parity to prevent regressions."""

import subprocess
from pathlib import Path


def test_cli_parity_never_slips():
    """Meta-test to ensure make cli-sweep always passes."""
    repo_root = Path(__file__).parent.parent

    # Run make cli-sweep
    result = subprocess.run(
        ["make", "cli-sweep"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    # Should exit with code 0 for success
    assert result.returncode == 0, f"CLI parity check failed:\n{result.stdout}\n{result.stderr}"

    # Output should contain all ✅ marks and no ❌
    assert "❌" not in result.stdout, f"CLI parity failures found:\n{result.stdout}"
    assert "✅" in result.stdout, f"Expected CLI parity checks not found:\n{result.stdout}"
