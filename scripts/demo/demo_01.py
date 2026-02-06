import json
import logging
import os
from importlib import resources
from logging.config import dictConfig
from pathlib import Path


import platformdirs
from omegaconf import OmegaConf

from saezlab_core.schema import validate_settings

# --- Start of this script

# CONSTANTS
ECOSYSTEM_CONFIG_FILENAME = "01_ecosystem.yaml"
DEFAULT_PACKAGE_CONFIG_FILENAME = "default_settings.yaml"
USER_CONFIG_FILENAME = "03_user.yaml"
WORKING_DIRECTORY_CONFIG_FILENAME = "04_workdir.yaml"

ENV_VARIABLE_DEFAULT_CONFIG = "SAEZLAB_CORE_CONFIG"


# Experimental functions
# [config.py]
def resolve_config_paths() -> dict[str, Path | None]:
	ecosystem_dir = Path(platformdirs.site_config_dir("saezlab_core"))
	user_dir = Path(platformdirs.user_config_dir("saezlab_core"))
	env_value = os.environ.get(ENV_VARIABLE_DEFAULT_CONFIG)

	return {
		"ecosystem": ecosystem_dir / ECOSYSTEM_CONFIG_FILENAME,
		"package": None,
		"user": user_dir / USER_CONFIG_FILENAME,
		"cwd": Path(WORKING_DIRECTORY_CONFIG_FILENAME),
		"env": Path(env_value) if env_value else None,
		"custom_path": None,
	}

# [config.py]
def read_package_default() -> OmegaConf:
	try:
		raw_config_text = (
			resources.files("saezlab_core.data")
			.joinpath(DEFAULT_PACKAGE_CONFIG_FILENAME)
			.read_text(encoding="utf-8")
		)
		return OmegaConf.create(raw_config_text)
	except FileNotFoundError:
		return OmegaConf.create({})

# [config.py]
def load_existing(path: Path | None) -> OmegaConf | None:
	if path and path.exists():
		return OmegaConf.load(path)
	return None

# [config.py]
def merge_configs(parts: list[OmegaConf]) -> OmegaConf:
	return OmegaConf.merge(*parts) if parts else OmegaConf.create({})

# [config.py]
def load_config(config_path: str | Path | None = None) -> OmegaConf:
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
			parts.append(load_existing(custom_path))

	return merge_configs([p for p in parts if p is not None])

# ===================================================================


# ===================================================================
def normalize_log_path(cfg: OmegaConf) -> None:
	"""Ensure file handler writes to user log dir."""
	if 'logging' not in cfg:
		return
	if 'handlers' not in cfg.logging:
		return
	if 'file' not in cfg.logging.handlers:
		return

	file_handler = cfg.logging.handlers.file
	filename = getattr(file_handler, 'filename', None)
	if not filename:
		return

	log_dir = Path(platformdirs.user_log_dir('saezlab_core'))
	log_dir.mkdir(parents=True, exist_ok=True)

	path = Path(filename)
	if not path.is_absolute():
		file_handler.filename = str(log_dir / path.name)

# [logger.py]
def create_logger():
	"""_summary_

	Returns:
		_type_: _description_
	"""
	logging_config = {
		"version": 1,
		"disable_existing_loggers": False,
		"formatters": {
			"f": {"format": "%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s"}
		},
		"handlers": {
			"cli": {
				"class": "logging.StreamHandler",
				"formatter": "f",
				"level": logging.INFO
			},
			"file":{
				"class": "logging.FileHandler",
				"formatter": "f",
				"level": logging.INFO,
				"filename": "logs/myapp.log",
			}
		},
		"root": {
			"handlers": ["cli", "file"],
			"level": logging.INFO
		}
	}

	Path("logs").mkdir(parents=True, exist_ok=True)
	dictConfig(logging_config)

	return logging.getLogger()

# ===============
# Main Function
# ===============

def main() -> None:

	#0. Create internal logger for this script
	logger = create_logger()

	#1. Start a session
	logger.info("Inicio de session: ")


	# at this point we need to create data for the session
	#    - id
	#    - user
	#    - workspace
	#    - started_at


	#2. Start configuration path inspection
	logger.debug(f'Discovered configuration paths: {resolve_config_paths()}')

	#3. Load and merge configuration files
	logger.debug("Load and merge configuration files")
	config_merged = load_config()

	#3.1 [optional] show configuration file merged
	cfg = OmegaConf.to_container(config_merged, resolve=True)
	logger.info("Final merged config:\n%s", json.dumps(cfg, indent=2, sort_keys=True, ensure_ascii=False))

	#4. Validate its schema.
	validate_settings(config_merged, show=False)

	#conf = load_config()

	#print(conf)

    #cfg = load_config()
	
    #print(cfg)

	# from omegaconf import OmegaConf as _OmegaConf
	# data = _OmegaConf.to_container(cfg, resolve=True)
	# pprint(data, sort_dicts=False)

	# normalize_log_path(cfg)
	# logging_cfg = _OmegaConf.to_container(cfg.logging, resolve=True)
	# pprint(logging_cfg, sort_dicts=False)

	# logging.config.dictConfig(logging_cfg)

	# logger = logging.getLogger('saezlab_infra')
	# logger.debug('This message should go to the log file')
	# logger.info('So should this')
	# logger.warning('And this, too')
	# logger.error('And non-ASCII stuff, too, like Øresund and Malmö')


if __name__ == '__main__':
	main()



# 1. Load the configuration for logging in OmegaConf
# 2. Convert OmagaConf object into a dictionary to pass it into logging.dictConfig()


#ideas
# it should useful to have a method to retrieve the current configuration settings