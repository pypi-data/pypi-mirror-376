from pathlib import Path
from sys import version_info
from tomllib import loads

from tomli_w import dump

OLD_PYTHON_MINOR_VERSION = 11

if version_info.minor == OLD_PYTHON_MINOR_VERSION:
    from importlib_resources import files
else:
    from importlib.resources import files


def write_config_to_file(config: dict, path: Path) -> None:
    with path.open("wb") as target_config_file:
        dump(config, target_config_file, multiline_strings=True)


def get_config_template() -> dict:
    assets = files(f"{__package__}.assets")
    sr_config_asset = assets.joinpath("toml").joinpath("semantic-release.toml").read_text(encoding="utf-8")

    config_template = loads(sr_config_asset)
    return config_template
