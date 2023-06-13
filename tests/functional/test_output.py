import subprocess
from pathlib import Path

import pytest
from git import Repo


class TestOutput:
    original_branch: str

    def test_output(
        self,
        output_testcase,
        repo: Repo,
        request: pytest.FixtureRequest,
        tmp_path_factory: pytest.TempPathFactory,
    ):
        update = request.config.getoption("--update-expected-outputs")

        repo.git.checkout(output_testcase.branch)

        run_result = subprocess.run(
            ["releaseherald", "generate", *output_testcase.commandline],
            capture_output=True,
            cwd=repo.working_dir,
        )

        expected_output_path = (
            Path(repo.working_dir) / "expected" / f"{output_testcase.name}.txt"
        )

        output = b"\n".join((run_result.stdout + b"\0").splitlines())[:-1]
        if not expected_output_path.exists() and not update:
            pytest.fail(f"Missing expected result: {expected_output_path}")

        if update:
            expected_output_path.parent.mkdir(parents=True, exist_ok=True)
            expected_output_path.write_bytes(output)

        expected_output = expected_output_path.read_bytes()

        assert output == expected_output
