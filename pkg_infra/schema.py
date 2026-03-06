from __future__ import annotations

import logging
from logging import NullHandler
from typing import Any, Dict, List, Optional, Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError

try:
	from omegaconf import OmegaConf
except ImportError:  # pragma: no cover - optional in pure schema usage
	OmegaConf = None


_logger = logging.getLogger(__name__)
_logger.addHandler(NullHandler())

# ---- Models

class AppCfg(BaseModel):
	model_config = ConfigDict(extra="forbid")

	name: Optional[str] = None
	environment: str
	logger: str


class EnvironmentProfile(BaseModel):
	model_config = ConfigDict(extra="forbid")

	name: str
	debug: bool


class SessionCfg(BaseModel):
	model_config = ConfigDict(extra="forbid")

	id: Optional[str] = None
	user: Optional[str] = None
	workspace: Optional[str] = None
	started_at: Optional[str] = None
	tags: List[str] = Field(default_factory=list)


class Settings(BaseModel):
	model_config = ConfigDict(extra="forbid")

	settings_version: str
	app: AppCfg
	environment: Dict[str, EnvironmentProfile]
	session: SessionCfg
	paths: Dict[str, Optional[str]]
	logging: Dict[str, Any]
	integrations: Dict[str, Any] = Field(default_factory=dict)
	ecosystems: Dict[str, List[str]] = Field(default_factory=dict)


def validate_settings(
	config: Mapping[str, Any] | Any,
	show: bool = False,
) -> bool:
	"""Validate a merged config.

	Returns True when valid. Raises ValidationError if invalid.
	"""
	data = config
	if OmegaConf is not None and OmegaConf.is_config(config):
		data = OmegaConf.to_container(config, resolve=True)

	try:
		validated = Settings.model_validate(data)
		_logger.info("Valid schema: True")
		if show:
			_logger.info(validated)
		return True
	except ValidationError:
		_logger.exception("Valid schema: False")
		raise

__all__ = [
	"AppCfg",
	"EnvironmentProfile",
	"SessionCfg",
	"Settings",
	"validate_settings",
]
