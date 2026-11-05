import datetime
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

import click
from git import Commit, TagReference  # type: ignore

from releaseherald.configuration import DefaultOptionsCallable

VT = TypeVar("VT")


@dataclass
class CommandOptions:
    """
    Represent a list of commandline options need to be registered to one of the
    cli command, together with a callable that can promote config settings as
    the default to the options.

    Attributes:
        options: list of options will be attached to a cli command
        default_options_callbacks:
            a callback that promote config settings to defaults to the above options
    """

    options: list[click.Option]
    default_opts_callback: DefaultOptionsCallable


class MutableProxy(Generic[VT]):
    """
    Generic proxy object to make it possible to mutate/replace params in
    consecutive hooks

    Attributes:
        value VT: the value the proxy holds
    """

    def __init__(self, value: VT | None = None):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value: VT | None):
        self._value = value


@dataclass
class CommitInfo:
    """
    Attributes:
        tag: The tag used to find this commit
        commit: The commit
        name: The name of the tag or "Unreleased"
        date:
            The date when the tag was attached to the commit if the tag is annotated,
            else the commit date
    """

    tag: TagReference | None
    commit: Commit

    @property
    def name(self) -> str:
        return self.tag.name if self.tag else "Unreleased"

    @property
    def date(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(
            self.tag.tag.tagged_date
            if self.tag and self.tag.tag
            else self.commit.committed_date
        )


@dataclass
class News:
    """
    Represent a single newsfile

    Attributes:
        file_name: file name of the news fragment
        content: the content of the news file
        metadata: a data store for plugins to attach extra data
    """

    file_name: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SubmoduleNews:
    """
    Represent a list of news for a given submodule.

    Attributes:
        name: The submodule name
        display_name: The display_name of the submodule
        news: The news
        metadata: a data store for plugins to attach extra data
    """

    name: str
    display_name: str
    news: list[News] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VersionNews:
    """
    Represent a given version with all the collected information

    Attributes:
        news: the list of news
        tag: the tag used to identigy this version
        from_commit: the earlier commit
        to_commit: the later commit
        date: date of this version
        submodule_news: news for every submodule for this release
        metadata: a data store for plugins to attach extra data
    """

    news: list[News]
    tag: str
    version: str
    from_commit: CommitInfo
    to_commit: CommitInfo
    date: datetime.datetime
    submodule_news: list[SubmoduleNews] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Output:
    """
    Represent the output rendered from the collected news for all the collected versions

    Attributes:
         format: could be used advertise the format of the content
         content: any plugin specific format
         metadata: a data store for plugins to attach extra data
    """

    format: str
    content: Any
    metadata: dict[str, Any] = field(default_factory=dict)
