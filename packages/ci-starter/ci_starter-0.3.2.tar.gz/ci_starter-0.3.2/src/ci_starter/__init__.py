from importlib.metadata import version as get_version
from logging import getLogger
from pathlib import Path

from .git_helpers import get_repo_name
from .helpers import get_config_template, write_config_to_file
from .presets import DISTRIBUTION_ARTIFACTS_DIR

__version__ = get_version(__package__)

logger = getLogger(__name__)


def generate_semantic_release_config(project_repo_path: Path, target_path: Path) -> None:
    repo_name = get_repo_name(project_repo_path)
    config: dict[str, str] = get_config_template()

    repo_dir_template: str = config["semantic_release"]["repo_dir"]
    actual_repo_dir: str = repo_dir_template.replace("PLACEHOLDER_REPO_NAME", repo_name)

    dist_glob_patterns_template: str = config["semantic_release"]["publish"]["dist_glob_patterns"]
    actual_dist_glob_patterns: str = dist_glob_patterns_template.replace(
        "PLACEHOLDER_DISTRIBUTION_ARTIFACTS_DIR", DISTRIBUTION_ARTIFACTS_DIR
    )

    config["semantic_release"]["repo_dir"] = actual_repo_dir
    config["semantic_release"]["publish"]["dist_glob_patterns"] = actual_dist_glob_patterns

    write_config_to_file(config, target_path)
