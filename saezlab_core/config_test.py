import json
import logging
import os
from importlib import resources
from logging.config import dictConfig
from pathlib import Path


import platformdirs
from omegaconf import OmegaConf
from pydantic import ValidationError

from saezlab_core.schema import validate_settings

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())


# CONSTANTS
ECOSYSTEM_CONFIG_FILENAME = "01_ecosystem.yaml"
DEFAULT_PACKAGE_CONFIG_FILENAME = "default_settings.yaml"
USER_CONFIG_FILENAME = "03_user.yaml"
WORKING_DIRECTORY_CONFIG_FILENAME = "04_workdir.yaml"
ENV_VARIABLE_DEFAULT_CONFIG = "SAEZLAB_CORE_CONFIG"


class ConfigLoader:
    """Loader for YAML configuration files with merging and priority logic.

    This class provides a static method to load and merge configuration files from
    package defaults, user directory, working directory, and an explicit path, returning
    a single merged DictConfig object.
    """

    # [config.py]
    @staticmethod
    def load_config(config_path: str | Path | None = None) -> OmegaConf:
        _logger.debug("Starting configuration load")
        paths = resolve_config_paths()
        parts = [
            load_existing(paths["ecosystem"]),
            read_package_default(),
            load_existing(paths["user"]),
            load_existing(paths["cwd"]),
            load_existing(paths["env"]),
        ]

        if config_path:
            custom_path = Path(config_path)
            if custom_path.exists():
                _logger.info("Loading custom config: %s", custom_path)
                parts.append(load_existing(custom_path))
            else:
                _logger.warning("Custom config path does not exist: %s", custom_path)

        config = merge_configs([p for p in parts if p is not None])

        _logger.debug("Validating merged configuration")
        try:
            validate_settings(config=config)
        except ValidationError:
            _logger.exception("Configuration schema validation failed")
            raise
        _logger.info("Configuration loaded and validated")
        return config

def resolve_config_paths() -> dict[str, Path | None]:
    ecosystem_dir = Path(platformdirs.site_config_dir("saezlab_core"))
    user_dir = Path(platformdirs.user_config_dir("saezlab_core"))
    env_value = os.environ.get(ENV_VARIABLE_DEFAULT_CONFIG)

    paths = {
        "ecosystem": ecosystem_dir / ECOSYSTEM_CONFIG_FILENAME,
        "package": None,
        "user": user_dir / USER_CONFIG_FILENAME,
        "cwd": Path(WORKING_DIRECTORY_CONFIG_FILENAME),
        "env": Path(env_value) if env_value else None,
        "custom_path": None,
    }
    _logger.debug("Resolved config paths: %s", paths)
    return paths

# [config.py]
def read_package_default() -> OmegaConf:
    try:
        _logger.debug("Loading package default config: %s", DEFAULT_PACKAGE_CONFIG_FILENAME)
        raw_config_text = (
            resources.files("saezlab_core.data")
            .joinpath(DEFAULT_PACKAGE_CONFIG_FILENAME)
            .read_text(encoding="utf-8")
        )
        return OmegaConf.create(raw_config_text)
    except FileNotFoundError:
        _logger.warning("Package default config not found: %s", DEFAULT_PACKAGE_CONFIG_FILENAME)
        return OmegaConf.create({})

# [config.py]
def load_existing(path: Path | None) -> OmegaConf | None:
    if path and path.exists():
        _logger.debug("Loading config file: %s", path)
        return OmegaConf.load(path)
    return None

# [config.py]
def merge_configs(parts: list[OmegaConf]) -> OmegaConf:
    return OmegaConf.merge(*parts) if parts else OmegaConf.create({})