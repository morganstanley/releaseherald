from functools import partial
from pathlib import Path
from shutil import rmtree

from doit.action import CmdAction

TESTS_DIR = Path("tests").absolute()
TEST_GIT_REPO_PATH = TESTS_DIR / "test_repo"
TEST_GIT_REPO_GIT_DIR = TEST_GIT_REPO_PATH / ".git"
TEST_GIT_REPO_PACK = TESTS_DIR / "test_repo.pack"

TestRepoAction = partial(CmdAction, cwd=TEST_GIT_REPO_PATH)


def task_unpack_tests():
    """unpack the test git repo"""

    return {
        "actions": [
            (rmtree, [], {"path": TEST_GIT_REPO_PATH, "ignore_errors": True}),
            f"git clone --mirror {TEST_GIT_REPO_PACK} {TEST_GIT_REPO_GIT_DIR}",
            TestRepoAction("git config --local --bool core.bare false"),
            TestRepoAction("git config --local core.autocrlf input"),
            TestRepoAction("git checkout main"),
            TestRepoAction("git reset --hard"),
        ]
    }


def task_pack_tests():
    """pack the test repo to prepare commit"""

    return {
        "actions": [TestRepoAction(f"git bundle create {TEST_GIT_REPO_PACK} --all")]
    }


def task_pytest():
    return {"actions": ["pytest tests"]}


def task_mypy():
    return {"actions": ["mypy src"]}


def task_lint():
    return {"actions": ["ruff check src"]}


def task_black():
    return {"actions": ["black --check src"]}


def task_testall():
    return {"actions": None, "task_dep": ["black", "lint", "pytest", "mypy"]}

