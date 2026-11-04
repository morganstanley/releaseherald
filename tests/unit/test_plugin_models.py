from releaseherald.plugins.base import GenerateParams
from releaseherald.plugins.metadata_extractor import FilenameMetadataExtractorConfig
from releaseherald.plugins.submodules import SubmoduleConfig, Submodules
from releaseherald.configuration import Configuration


def test_generate_params_optional_target():
    params = GenerateParams(update=True, unreleased=False)

    assert params.target is None


def test_metadata_extractor_optional_target_attribute():
    config = FilenameMetadataExtractorConfig.model_validate(
        {"type": "re", "pattern": r"(?P<id>\d+)"}
    )

    assert config.target_attribute is None


def test_submodule_display_name_defaults_to_name():
    assert SubmoduleConfig(name="sub").display_name == "sub"
    assert SubmoduleConfig(name="sub", display_name="Sub").display_name == "Sub"


def test_submodules_parsed_from_config():
    config = Configuration.model_validate(
        {
            "config_path": "pyproject.toml",
            "submodules": [
                {"name": "first"},
                {"name": "second", "version_tag_pattern": r"v(?P<version>.*)"},
            ],
        }
    )

    plugin = Submodules()
    plugin.process_config(config)

    assert [s.display_name for s in plugin.submodule_config] == ["first", "second"]
    assert plugin.submodule_config[1].version_tag_pattern.match("v1.0")
    assert config.submodules is plugin.submodule_config
