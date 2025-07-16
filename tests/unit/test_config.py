import pytest

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
        _ = Configuration.parse_obj(config_d)
