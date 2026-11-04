from pathlib import Path
from typing import Optional

import pytest
from pydantic import BaseModel

from releaseherald.configuration import Configuration


@pytest.mark.parametrize(
    "config_d",
    [
        {
            "config_path": "pyproject.toml",
            "last_tag": "v1.0.0",
        },
        {
            "config_path": "pyproject.toml",
            "last_tag": "v2.0.0",
            "version_tag_pattern": r"(?P<version>(\d+)\.(\d+)\.(\d+))",
        },
    ],
)
def test_bad_last_tag(config_d):
    with pytest.raises(
        ValueError, match=r".*last_tag...must match...version_tag_pattern.*"
    ):
        _ = Configuration.model_validate(config_d)


def test_paths_resolved_relative_to_config_file(tmp_path):
    config_file = tmp_path / "pyproject.toml"
    config_file.touch()

    config = Configuration.model_validate(
        {"config_path": config_file, "news_file": "docs/news.md"}
    )

    assert config.news_file == tmp_path / "docs" / "news.md"
    assert config.template.is_absolute()


def test_extra_paths_to_resolve(tmp_path, monkeypatch):
    monkeypatch.setattr(
        Configuration,
        "paths_to_resolve",
        [*Configuration.paths_to_resolve, "plugin_path"],
    )

    config = Configuration.model_validate(
        {"config_path": tmp_path, "plugin_path": "some/file"}
    )

    assert config.plugin_path == tmp_path / "some" / "file"


def test_patterns_parsed_from_string():
    config = Configuration.model_validate(
        {"config_path": "pyproject.toml", "version_tag_pattern": r"v(?P<version>.*)"}
    )

    assert config.version_tag_pattern.match("v1.2.3").group("version") == "1.2.3"


def test_default_options_callbacks():
    config = Configuration(config_path=Path("pyproject.toml"))

    def callback(options):
        options["unreleased"] = True

    callbacks = Configuration.default_options_callbacks["generate"]
    callbacks.append(callback)
    try:
        assert config.as_default_options()["generate"]["unreleased"] is True
    finally:
        callbacks.remove(callback)


class SubConfig(BaseModel):
    value: int
    label: Optional[str] = None


def test_parse_sub_config():
    config = Configuration.model_validate(
        {"config_path": "pyproject.toml", "my_plugin": {"value": "42"}}
    )

    sub_config = config.parse_sub_config("my_plugin", SubConfig)

    assert sub_config == SubConfig(value=42)
    assert config.my_plugin is sub_config


def test_parse_missing_sub_config():
    config = Configuration(config_path=Path("pyproject.toml"))

    assert config.parse_sub_config("missing", SubConfig) is None
    assert config.missing is None
