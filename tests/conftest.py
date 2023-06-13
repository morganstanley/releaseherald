import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Iterator

import pytest
from git import Repo


@dataclass
class OutputTestcase:
    name: str
    branch: str
    commandline: List[str]


TEST_REPO_PATH = Path(__file__).parent / "test_repo"


@pytest.fixture(scope="class")
def repo() -> Iterator[Repo]:
    repo = Repo(TEST_REPO_PATH)
    branch = repo.active_branch.name

    yield repo

    repo.git.checkout(branch)


def collect_output_testcases(current_branch: bool = False):
    repo = Repo(TEST_REPO_PATH)
    if current_branch:
        branches = [repo.active_branch.name]
    else:
        path = repo.heads.main.commit.tree / "tests.json"
        branches = json.load(io.BytesIO(path.data_stream.read()))

    result: List[OutputTestcase] = []

    for branch in branches:
        case_file = repo.heads[branch].commit.tree / "cases.json"
        cases = json.load(io.BytesIO(case_file.data_stream.read()))
        result.extend(OutputTestcase(branch=branch, **case) for case in cases)

    return result


def pytest_generate_tests(metafunc: pytest.Metafunc):
    if "output_testcase" in metafunc.fixturenames:
        # discover output testcases
        cases = collect_output_testcases(
            current_branch=metafunc.config.getoption("--current-branch")
            or metafunc.config.getoption(
                "--update-expected-outputs"
            )  # on update only run checked out branch
        )
        metafunc.parametrize(
            "output_testcase",
            cases,
            indirect=True,
            ids=lambda case: f"{case.branch}:{case.name}",
        )


@pytest.fixture
def output_testcase(request) -> OutputTestcase:
    return request.param


def pytest_addoption(parser: pytest.Parser):
    parser.addoption("--update-expected-outputs", action="store_true")
    parser.addoption("--current-branch", action="store_true")
