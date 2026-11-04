from typing import Annotated

import click
import pytest

from releaseherald.plugins.plugin_config import FromCommandline, PluginConfig


class MyPluginConfig(PluginConfig):
    plain: str = "plain"
    overridable: Annotated[
        str,
        FromCommandline(
            "generate",
            click.Option(param_decls=["--override"], help="override the value"),
        ),
    ] = "default"


def test_command_options_from_annotations():
    config = MyPluginConfig()

    command_options = config.get_command_options("generate")

    assert command_options is not None
    assert [option.name for option in command_options.options] == ["override"]

    defaults: dict = {}
    command_options.default_opts_callback(defaults)
    assert defaults == {"override": "default"}


def test_no_command_options_for_other_command():
    assert MyPluginConfig().get_command_options("other") is None


def test_update_from_commandline():
    config = MyPluginConfig()

    config.update("generate", {"override": "from commandline"})

    assert config.overridable == "from commandline"
    assert config.plain == "plain"


def test_option_without_name():
    class BadPluginConfig(PluginConfig):
        value: Annotated[
            str,
            FromCommandline(
                "generate", click.Option(param_decls=[], expose_value=False)
            ),
        ] = ""

    with pytest.raises(AttributeError, match="value field config option"):
        BadPluginConfig().get_command_options("generate")
