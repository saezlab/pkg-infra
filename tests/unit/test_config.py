"""
Unit tests for configuration loading utilities.

Unit test organization:
    - Nominal Case Tests: Test the nominal case where the function is expected
      to work correctly with typical input values.

    - Negative Case Tests: Test cases that involve invalid input values or
      scenarios where the function should handle errors gracefully.

    - Edge Case Tests: Test cases that involve boundary conditions or unusual
      input values that may not be common but should still be handled correctly
      by the function.

    - Regression Unit Tests: Test cases that ensure that previously fixed bugs
      do not reoccur and that existing functionality remains intact after
      changes to the codebase.
"""

from __future__ import annotations

# Standard imports
import logging
from datetime import datetime, timezone
from pathlib import Path

# Third-party imports
import pytest
from omegaconf import OmegaConf
from pydantic import ValidationError

# Local imports
from pkg_infra.config import (
    ECOSYSTEM_CONFIG_FILENAME,
    USER_CONFIG_FILENAME,
    WORKING_DIRECTORY_CONFIG_FILENAME,
    ConfigLoader,
    load_existing,
    merge_configs,
    omegaconf_to_plain_dict,
    read_package_default,
    resolve_config_paths,
)

__all__ = [
    'TestConfigLoader',
    'TestLoadExisting',
    'TestMergeConfigs',
    'TestReadPackageDefault',
    'invalid_yaml_path',
    'resources_dir',
    'valid_yaml_path',
]


# =============================================================================
# ==== Fixtures and Setup
# =============================================================================
@pytest.fixture
def resources_dir() -> Path:
    """Fixture to provide the directory containing YAML resource files."""
    return Path(__file__).resolve().parents[1] / 'resources'


@pytest.fixture
def valid_yaml_path(resources_dir: Path) -> Path:
    """Fixture to provide the valid YAML resource path."""
    return resources_dir / 'valid.yaml'


@pytest.fixture
def invalid_yaml_path(resources_dir: Path) -> Path:
    """Fixture to provide the invalid YAML resource path."""
    return resources_dir / 'invalid.yaml'


# =============================================================================
# ==== Class Test Cases
# =============================================================================
class TestReadPackageDefault:
    """Test cases for read_package_default."""

    # ---- Nominal Case Tests
    def test_nominal_case(self) -> None:
        """Test that the packaged default YAML loads successfully."""
        config = read_package_default()

        assert OmegaConf.is_config(config)

    # ---- Regression Unit Tests
    def test_loaded_default_config_contains_expected_top_level_keys(
        self,
    ) -> None:
        """Test that default config keeps the expected baseline keys."""
        config = read_package_default()

        assert config.settings_version == '0.0.1'
        assert 'app' in config
        assert 'logging' in config

    # ---- Edge Case Tests
    def test_missing_packaged_default_returns_empty_config(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Return an empty config when the packaged default is unavailable."""
        from pkg_infra import config as config_module

        class _MissingResource:
            def joinpath(self, _filename: str) -> '_MissingResource':
                return self

            def read_text(self, encoding: str = 'utf-8') -> str:
                raise FileNotFoundError('missing resource')

        monkeypatch.setattr(
            config_module.resources,
            'files',
            lambda _package: _MissingResource(),
        )

        config = read_package_default()

        assert OmegaConf.to_container(config, resolve=True) == {}


class TestLoadExisting:
    """Test cases for load_existing."""

    # ---- Nominal Case Tests
    def test_nominal_case(self, valid_yaml_path: Path) -> None:
        """Test that an existing YAML file is loaded."""
        config = load_existing(valid_yaml_path)

        assert config is not None
        assert config.app.name == 'demo'

    # ---- Negative Case Tests
    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        """Test that a missing file path returns None."""
        missing_path = tmp_path / 'missing.yaml'

        assert load_existing(missing_path) is None

    # ---- Edge Case Tests
    def test_none_input_returns_none(self) -> None:
        """Test that None input is handled gracefully."""
        assert load_existing(None) is None

    # ---- Edge Case Tests
    def test_directory_path_raises_omegaconf_error(self, tmp_path: Path) -> None:
        """Surface OmegaConf errors when the given path is not a file."""
        with pytest.raises(Exception):
            load_existing(tmp_path)


class TestMergeConfigs:
    """Test cases for merge_configs."""

    # ---- Nominal Case Tests
    def test_later_configs_override_earlier_ones(self) -> None:
        """Test that later configurations win during merge."""
        base = OmegaConf.create({'app': {'name': 'base'}})
        override = OmegaConf.create({'app': {'name': 'override'}})

        merged = merge_configs([base, override])

        assert merged.app.name == 'override'

    # ---- Edge Case Tests
    def test_empty_input_returns_empty_config(self) -> None:
        """Test that merging no configs returns an empty config."""
        merged = merge_configs([])

        assert OmegaConf.to_container(merged, resolve=True) == {}

    def test_single_config_remains_effectively_unchanged(self) -> None:
        """Test that merging one config preserves its values."""
        single = OmegaConf.create({'app': {'name': 'demo'}})

        merged = merge_configs([single])

        assert merged.app.name == 'demo'

    # ---- Regression Unit Tests
    def test_merge_precedence_remains_stable(self) -> None:
        """Test that the last config keeps highest precedence."""
        first = OmegaConf.create({'paths': {'log_dir': 'first'}})
        second = OmegaConf.create({'paths': {'log_dir': 'second'}})
        third = OmegaConf.create({'paths': {'log_dir': 'third'}})

        merged = merge_configs([first, second, third])

        assert merged.paths.log_dir == 'third'


class TestResolveConfigPaths:
    """Test cases for resolve_config_paths."""

    # ---- Nominal Case Tests
    def test_env_path_is_resolved_when_set(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Return an env-config path when the env var is defined."""
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.site_config_dir',
            lambda _appname: str(tmp_path / 'site'),
        )
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.user_config_dir',
            lambda _appname: str(tmp_path / 'user'),
        )
        monkeypatch.setenv('PKG_INFRA_CONFIG', str(tmp_path / 'env.yaml'))

        paths = resolve_config_paths()

        assert paths['env'] == tmp_path / 'env.yaml'

    # ---- Edge Case Tests
    def test_env_path_is_none_when_env_var_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Leave the env path unset and log the missing variable."""
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.site_config_dir',
            lambda _appname: str(tmp_path / 'site'),
        )
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.user_config_dir',
            lambda _appname: str(tmp_path / 'user'),
        )
        monkeypatch.delenv('PKG_INFRA_CONFIG', raising=False)
        calls: list[tuple[str, str]] = []
        monkeypatch.setattr(
            'pkg_infra.config.logger.debug',
            lambda message, *args: calls.append((message, args[0])),
        )

        paths = resolve_config_paths()

        assert paths['env'] is None
        assert calls == [('Env var %s not set; skipping env config', 'PKG_INFRA_CONFIG')]


class TestOmegaConfToPlainDict:
    """Test cases for omegaconf_to_plain_dict."""

    # ---- Nominal Case Tests
    def test_omegaconf_input_becomes_plain_containers(self) -> None:
        """Convert OmegaConf objects into plain Python containers."""
        config = OmegaConf.create({'app': {'name': 'demo'}, 'items': [1, 2]})

        plain = omegaconf_to_plain_dict(config)

        assert plain == {'app': {'name': 'demo'}, 'items': [1, 2]}
        assert isinstance(plain, dict)

    # ---- Regression Unit Tests
    def test_plain_dict_input_is_deep_copied(self) -> None:
        """Return a deep copy so callers cannot mutate the original input."""
        source = {'app': {'name': 'demo'}}

        plain = omegaconf_to_plain_dict(source)
        plain['app']['name'] = 'changed'

        assert source['app']['name'] == 'demo'

    # ---- Edge Case Tests
    def test_plain_list_input_is_copied_recursively(self) -> None:
        """Recursively copy nested lists and dictionaries."""
        source = [{'app': {'name': 'demo'}}]

        plain = omegaconf_to_plain_dict(source)
        plain[0]['app']['name'] = 'changed'

        assert source[0]['app']['name'] == 'demo'


class TestTimestampUtility:
    """Test cases for timestamp utility behavior."""

    # ---- Nominal Case Tests
    def test_get_timestamp_now_returns_utc_timestamp_with_z_suffix(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Return a filesystem-safe UTC timestamp with an explicit Z suffix."""
        import pkg_infra.utils as utils_module

        class FrozenDateTime(datetime):
            """Frozen datetime class for deterministic timestamp tests."""

            @classmethod
            def now(cls, tz=None):  # type: ignore[override]
                return cls(2026, 3, 31, 12, 30, 36, tzinfo=timezone.utc)

        monkeypatch.setattr(utils_module.datetime, 'datetime', FrozenDateTime)

        assert utils_module.get_timestamp_now() == '20260331T123036Z'


class TestConfigLoader:
    """Test cases for ConfigLoader.load_config."""

    # ---- Nominal Case Tests
    def test_valid_custom_yaml_loads_successfully(
        self,
        valid_yaml_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test that a valid custom YAML file loads and validates."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.site_config_dir',
            lambda appname: str(tmp_path / 'site_config'),
        )
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.user_config_dir',
            lambda appname: str(tmp_path / 'user_config'),
        )
        monkeypatch.delenv('PKG_INFRA_CONFIG', raising=False)

        config = ConfigLoader.load_config(valid_yaml_path)

        assert config.app.name == 'demo'

    def test_package_default_loads_through_full_loader(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test that the full loader can load the packaged defaults."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.site_config_dir',
            lambda appname: str(tmp_path / 'site_config'),
        )
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.user_config_dir',
            lambda appname: str(tmp_path / 'user_config'),
        )
        monkeypatch.delenv('PKG_INFRA_CONFIG', raising=False)

        config = ConfigLoader.load_config()

        assert config.settings_version == '0.0.1'
        assert config.app.name is None

    # ---- Negative Case Tests
    def test_invalid_schema_raises_validation_error(
        self,
        invalid_yaml_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test that invalid schema input raises ValidationError."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.site_config_dir',
            lambda appname: str(tmp_path / 'site_config'),
        )
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.user_config_dir',
            lambda appname: str(tmp_path / 'user_config'),
        )
        monkeypatch.delenv('PKG_INFRA_CONFIG', raising=False)

        with pytest.raises(ValidationError):
            ConfigLoader.load_config(invalid_yaml_path)

    def test_missing_explicit_custom_path_is_ignored(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that a missing explicit custom path does not crash the load."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.site_config_dir',
            lambda appname: str(tmp_path / 'site_config'),
        )
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.user_config_dir',
            lambda appname: str(tmp_path / 'user_config'),
        )
        monkeypatch.delenv('PKG_INFRA_CONFIG', raising=False)

        with caplog.at_level('WARNING'):
            config = ConfigLoader.load_config(tmp_path / 'missing.yaml')

        assert config.settings_version == '0.0.1'
        assert 'Custom config path does not exist' in caplog.text

    # ---- Edge Case Tests
    def test_absent_optional_config_sources_do_not_break_loading(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test that missing optional sources are skipped safely."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.site_config_dir',
            lambda appname: str(tmp_path / 'site_config'),
        )
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.user_config_dir',
            lambda appname: str(tmp_path / 'user_config'),
        )
        monkeypatch.delenv('PKG_INFRA_CONFIG', raising=False)

        config = ConfigLoader.load_config()

        assert config.app.environment == 'dev'

    # ---- Regression Unit Tests
    def test_validation_failure_logs_explicit_field_names(
        self,
        invalid_yaml_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that validation logs include offending field names."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.site_config_dir',
            lambda appname: str(tmp_path / 'site_config'),
        )
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.user_config_dir',
            lambda appname: str(tmp_path / 'user_config'),
        )
        monkeypatch.delenv('PKG_INFRA_CONFIG', raising=False)

        with pytest.raises(ValidationError):
            ConfigLoader.load_config(invalid_yaml_path)

        assert (
            'Configuration loading failed during schema validation'
            in caplog.text
        )
        assert 'my_custon_field_app' in caplog.text

    def test_validation_failure_initializes_root_logging_when_needed(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Configure basic logging before reporting schema failures."""
        error = ValidationError.from_exception_data(
            'Settings',
            [
                {
                    'type': 'missing',
                    'loc': ('app',),
                    'msg': 'Field required',
                    'input': {},
                },
            ],
        )

        monkeypatch.setattr(
            'pkg_infra.config.resolve_config_paths',
            lambda: {
                'ecosystem': None,
                'package': None,
                'user': None,
                'cwd': None,
                'env': None,
                'custom_path': None,
            },
        )
        monkeypatch.setattr(
            'pkg_infra.config.read_package_default',
            lambda: OmegaConf.create({}),
        )
        monkeypatch.setattr('pkg_infra.config.load_existing', lambda _path: None)
        monkeypatch.setattr(
            'pkg_infra.config.validate_settings',
            lambda config: (_ for _ in ()).throw(error),
        )

        original_get_logger = logging.getLogger
        calls: list[int] = []
        monkeypatch.setattr(
            'pkg_infra.config.logging.basicConfig',
            lambda *, level: calls.append(level),
        )
        monkeypatch.setattr(
            'pkg_infra.config.logging.getLogger',
            lambda *args, **kwargs: original_get_logger(*args, **kwargs),
        )
        original_get_logger().handlers.clear()
        error_messages: list[str] = []
        monkeypatch.setattr(
            'pkg_infra.config.logger.error',
            lambda message, *args: error_messages.append(message),
        )

        with pytest.raises(ValidationError):
            ConfigLoader.load_config()

        assert calls == [logging.ERROR]
        assert error_messages == [
            'Configuration loading failed during schema validation with %d error(s): %s',
        ]

    def test_env_config_keeps_highest_precedence(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test that environment-config file overrides lower-priority sources."""
        site_dir = tmp_path / 'site_config'
        user_dir = tmp_path / 'user_config'
        site_dir.mkdir()
        user_dir.mkdir()

        (site_dir / ECOSYSTEM_CONFIG_FILENAME).write_text(
            'settings_version: 0.0.1\napp:\n  name: ecosystem\n',
            encoding='utf-8',
        )
        (user_dir / USER_CONFIG_FILENAME).write_text(
            'app:\n  name: user\n',
            encoding='utf-8',
        )
        (tmp_path / WORKING_DIRECTORY_CONFIG_FILENAME).write_text(
            'app:\n  name: workdir\n',
            encoding='utf-8',
        )
        env_path = tmp_path / 'env.yaml'
        env_path.write_text(
            'app:\n  name: env\n',
            encoding='utf-8',
        )

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.site_config_dir',
            lambda appname: str(site_dir),
        )
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.user_config_dir',
            lambda appname: str(user_dir),
        )
        monkeypatch.setenv('PKG_INFRA_CONFIG', str(env_path))

        config = ConfigLoader.load_config()

        assert config.app.name == 'env'

    def test_full_source_priority_order_is_applied(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test that the full source priority chain is respected."""
        site_dir = tmp_path / 'site_config'
        user_dir = tmp_path / 'user_config'
        site_dir.mkdir()
        user_dir.mkdir()

        (site_dir / ECOSYSTEM_CONFIG_FILENAME).write_text(
            'settings_version: 0.0.1\napp:\n  name: ecosystem\n',
            encoding='utf-8',
        )
        (user_dir / USER_CONFIG_FILENAME).write_text(
            'app:\n  name: user\n',
            encoding='utf-8',
        )
        (tmp_path / WORKING_DIRECTORY_CONFIG_FILENAME).write_text(
            'app:\n  name: workdir\n',
            encoding='utf-8',
        )
        env_path = tmp_path / 'env.yaml'
        env_path.write_text(
            'app:\n  name: env\n',
            encoding='utf-8',
        )
        custom_path = tmp_path / 'custom.yaml'
        custom_path.write_text(
            'app:\n  name: custom\n',
            encoding='utf-8',
        )

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.site_config_dir',
            lambda appname: str(site_dir),
        )
        monkeypatch.setattr(
            'pkg_infra.config.platformdirs.user_config_dir',
            lambda appname: str(user_dir),
        )
        monkeypatch.setenv('PKG_INFRA_CONFIG', str(env_path))

        config = ConfigLoader.load_config(custom_path)

        assert config.app.name == 'custom'
