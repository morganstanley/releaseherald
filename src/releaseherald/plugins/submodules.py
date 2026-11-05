from pathlib import Path
from re import Pattern

from boltons.iterutils import pairwise
from git import Commit, Repo  # type: ignore
from pydantic import BaseModel, TypeAdapter, model_validator

import releaseherald.plugins
from releaseherald.configuration import (
    DEFAULT_FRAGMENTS_DIR,
    DEFAULT_VERSION_TAG_PATTERN,
    Configuration,
)
from releaseherald.plugins.base import get_news_between_commits, get_tags
from releaseherald.plugins.interface import (
    CommitInfo,
    MutableProxy,
    News,
    SubmoduleNews,
    VersionNews,
)


class SubmoduleConfig(BaseModel):
    r"""
    Attributes:
        name: The name of the submodule as referenced by git
        display_name: This name is passed to the rendering to be used. **_Default:_** same as `name`
        news_fragments_directory: the news fragment directory relative to submodule root. **_Default:_** `news_fragment`
        version_tag_pattern: The version tag pattern in this submodule. **_Default:_** `"(?P<version>(\d*)\.(\d*)\.(\d*))"`
    """

    name: str
    display_name: str | None = None
    news_fragments_directory: Path = DEFAULT_FRAGMENTS_DIR
    version_tag_pattern: Pattern = DEFAULT_VERSION_TAG_PATTERN

    @model_validator(mode="after")
    def default_display_name(self) -> "SubmoduleConfig":
        self.display_name = self.display_name or self.name
        return self


class Submodules:
    def __init__(self) -> None:
        self.config: Configuration | None = None
        self.submodule_config: list[SubmoduleConfig] = []

    @releaseherald.plugins.hookimpl
    def process_config(self, config: Configuration):
        self.config = config
        submodules = getattr(config, "submodules", None)

        if submodules:
            self.submodule_config = TypeAdapter(list[SubmoduleConfig]).validate_python(
                submodules
            )

        # `submodules` is an extra (undeclared) field, so mypy needs setattr here
        setattr(config, "submodules", self.submodule_config)  # noqa: B010

    @releaseherald.plugins.hookimpl
    def get_version_news(
        self,
        repo: Repo,
        commit_from: CommitInfo,
        commit_to: CommitInfo,
        news: list[News],
        version_news: MutableProxy[VersionNews],
    ):
        submodule_news = get_submodule_news(
            commit_from.commit, commit_to.commit, self.submodule_config
        )
        version_news.value.submodule_news = submodule_news


def get_submodule_commit(commit: Commit, name: str) -> Commit | None:
    repo = commit.repo
    try:
        submodule = repo.submodules[name]
        sha = (commit.tree / submodule.path).hexsha
    except KeyError:
        # this case the submodule either not exist or not exist at that commit we are looking into
        return None

    srepo = submodule.module()
    return srepo.commit(sha)


def get_submodule_news(
    commit_from: Commit, commit_to: Commit, submodules: list[SubmoduleConfig]
) -> list[SubmoduleNews]:
    news = []
    for submodule in submodules:
        submodule_from = get_submodule_commit(commit_from, submodule.name)
        submodule_to = get_submodule_commit(commit_to, submodule.name)

        if not submodule_from or not submodule_to:
            continue

        srepo = submodule_from.repo
        tag_commits = [
            tag.commit
            for tag in get_tags(srepo, submodule.version_tag_pattern)
            if srepo.is_ancestor(submodule_from, tag.commit)
            and srepo.is_ancestor(tag.commit, submodule_to)
        ]

        commits = [submodule_to, *tag_commits, submodule_from]

        snews = SubmoduleNews(
            name=submodule.name, display_name=submodule.display_name or submodule.name
        )

        for c_to, c_from in pairwise(commits):
            snews.news.extend(
                get_news_between_commits(
                    c_from, c_to, submodule.news_fragments_directory
                )
            )
        news.append(snews)
    return news
