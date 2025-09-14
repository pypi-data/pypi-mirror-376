from importlib.metadata import version as get_version
from logging import getLogger
from pathlib import Path

from .git_helpers import get_repo_name
from .helpers import get_config_template, write_config_to_file

__version__ = get_version(__package__)

logger = getLogger(__name__)


def generate_semantic_release_config(project_repo_path: Path, target_path: Path) -> None:
    repo_name = get_repo_name(project_repo_path)
    config: dict[str, str] = get_config_template()

    repo_dir_template: str = config["semantic_release"]["repo_dir"]
    actual_repo_dir: str = repo_dir_template.replace("PLACEHOLDER_REPO_NAME", repo_name)

    config["semantic_release"]["repo_dir"] = actual_repo_dir

    write_config_to_file(config, target_path)
