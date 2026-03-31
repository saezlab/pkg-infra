"""
Unit tests for the logger module.

Unit test organization:
    - Nominal Case Tests: Test the nominal case where the function is
      expected to work correctly with typical input values.
    - Negative Case Tests: Test cases that involve invalid input values
      or scenarios where the function should handle errors gracefully.
    - Edge Case Tests: Test cases that involve boundary conditions or
      unusual input values that may not be common but should still be
      handled correctly by the function.
    - Regression Unit Tests: Test cases that ensure that previously
      fixed bugs do not reoccur and that existing functionality remains
      intact after changes to the codebase.
"""

from __future__ import annotations

# Standard imports
import io
import json
import logging
from logging.handlers import QueueHandler
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Third-party imports
import pytest
import yaml
from omegaconf import OmegaConf

# Local imports
from pkg_infra.logger import (
    get_logger,
    initialize_logging,
    initialize_logging_from_config,
    is_logging_initialized,
    list_loggers,
)


# =============================================================================
# ==== Fixtures and Setup
# =============================================================================
@pytest.fixture(autouse=True)
def isolate_environment(tmp_path: Path):
    """Reset the logging runtime between tests."""
    logging.shutdown()
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.Logger.manager.loggerDict.clear()

    from pkg_infra import logger as logger_module

    logger_module._stop_async_logging_listener()
    logger_module._logging_initialized = False

    yield

    for log_dir in tmp_path.glob('**/logs'):
        shutil.rmtree(log_dir, ignore_errors=True)

    logging.shutdown()
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.Logger.manager.loggerDict.clear()
    logger_module._stop_async_logging_listener()
    logger_module._logging_initialized = False


@pytest.fixture
def minimal_config(tmp_path: Path) -> dict:
    """Return a valid merged config for logger initialization tests."""
    log_dir = tmp_path / 'logs'

    return {
        'settings_version': '0.0.1',
        'app': {
            'environment': 'test',
            'logger': 'default',
        },
        'logging': {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {'format': '%(levelname)s:%(name)s:%(message)s'},
            },
            'handlers': {
                'file': {
                    'class': 'logging.FileHandler',
                    'formatter': 'default',
                    'filename': str(log_dir / 'test.log'),
                    'level': 'info',
                },
                'null': {
                    'class': 'logging.NullHandler',
                    'formatter': 'default',
                    'level': 'NOTSET',
                },
            },
            'loggers': {
                'default': {
                    'handlers': ['file'],
                    'level': 'info',
                    'propagate': False,
                },
                'test_logger': {
                    'handlers': ['file'],
                    'level': 'info',
                    'propagate': False,
                },
            },
            'filters': {},
            'root': {
                'level': 'warning',
                'handlers': [],
            },
        },
        'integrations': {},
        'packages_groups': {},
    }


@pytest.fixture
def fallback_config(tmp_path: Path) -> dict:
    """Return a config whose root logger depends on fallback handlers."""
    return {
        'settings_version': '0.0.1',
        'app': {
            'environment': 'test',
            'logger': 'default',
        },
        'logging': {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {'format': '%(message)s'},
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'default',
                    'stream': 'ext://sys.stdout',
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'formatter': 'default',
                    'filename': str(tmp_path / 'logs' / 'root.log'),
                },
                'null': {
                    'class': 'logging.NullHandler',
                    'formatter': 'default',
                    'level': 'NOTSET',
                },
            },
            'loggers': {
                'default': {
                    'handlers': ['console'],
                    'level': 'info',
                    'propagate': False,
                },
            },
            'filters': {},
            'root': {'level': 'warning', 'handlers': []},
        },
        'integrations': {},
        'packages_groups': {},
    }


@pytest.fixture
def json_logging_config(tmp_path: Path) -> dict:
    """Return a config that enables JSON output for file handlers."""
    return {
        'settings_version': '0.0.1',
        'app': {
            'environment': 'test',
            'logger': 'default',
        },
        'logging': {
            'version': 1,
            'disable_existing_loggers': False,
            'file_output_format': 'json',
            'formatters': {
                'default': {'format': '%(levelname)s:%(name)s:%(message)s'},
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'default',
                    'stream': 'ext://sys.stdout',
                    'level': 'INFO',
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'formatter': 'default',
                    'filename': str(tmp_path / 'logs' / 'json_log.log'),
                    'level': 'INFO',
                },
                'null': {
                    'class': 'logging.NullHandler',
                    'formatter': 'default',
                    'level': 'NOTSET',
                },
            },
            'loggers': {
                'default': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': False,
                },
                'json_logger': {
                    'handlers': ['file'],
                    'level': 'INFO',
                    'propagate': False,
                },
            },
            'filters': {},
            'root': {'level': 'warning', 'handlers': []},
        },
        'integrations': {},
        'packages_groups': {},
    }


@pytest.fixture
def initialized_logging(minimal_config: dict) -> dict:
    """Initialize logging for tests that need the runtime configured."""
    initialize_logging_from_config(minimal_config)
    return minimal_config


@pytest.fixture
def async_logging_config(tmp_path: Path) -> dict:
    """Return a config that enables async queue-based logging."""
    log_dir = tmp_path / 'logs'

    return {
        'settings_version': '0.0.1',
        'app': {
            'environment': 'test',
            'logger': 'default',
        },
        'logging': {
            'version': 1,
            'disable_existing_loggers': False,
            'file_output_format': 'text',
            'async_mode': True,
            'queue_maxsize': 1000,
            'formatters': {
                'default': {'format': '%(levelname)s:%(name)s:%(message)s'},
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'default',
                    'stream': 'ext://sys.stdout',
                    'level': 'INFO',
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'formatter': 'default',
                    'filename': str(log_dir / 'async.log'),
                    'level': 'INFO',
                },
                'null': {
                    'class': 'logging.NullHandler',
                    'formatter': 'default',
                    'level': 'NOTSET',
                },
            },
            'loggers': {
                'default': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': False,
                },
                'async_logger': {
                    'handlers': ['file'],
                    'level': 'INFO',
                    'propagate': False,
                },
            },
            'filters': {},
            'root': {'level': 'warning', 'handlers': []},
        },
        'integrations': {},
        'packages_groups': {},
    }


class TestInitializeLogging:
    """Tests for public initialization entry points."""

    # ---- Nominal Case Tests
    def test_initialize_and_write_log(
        self,
        initialized_logging: dict,
        tmp_path: Path,
    ) -> None:
        configured_logger = get_logger('test_logger')
        configured_logger.info('hello')

        log_files = list((tmp_path / 'logs').glob('test_*.log'))
        assert log_files
        assert any('hello' in path.read_text() for path in log_files)

    def test_initialize_from_file(
        self,
        minimal_config: dict,
        tmp_path: Path,
    ) -> None:
        config_path = tmp_path / 'config.yaml'
        OmegaConf.save(minimal_config, config_path)

        initialize_logging(str(config_path))

        assert is_logging_initialized()

    # ---- Edge Case Tests
    def test_initialize_with_omegaconf(self, minimal_config: dict) -> None:
        config = OmegaConf.create(minimal_config)

        initialize_logging_from_config(config)

        assert is_logging_initialized()

    # ---- Regression Unit Tests
    def test_initialize_is_idempotent(self, minimal_config: dict) -> None:
        initialize_logging_from_config(minimal_config)
        initialize_logging_from_config(minimal_config)

        assert is_logging_initialized()

    # ---- Regression Unit Tests
    def test_no_duplicate_root_handlers(self, minimal_config: dict) -> None:
        initialize_logging_from_config(minimal_config)
        before = len(logging.getLogger().handlers)

        initialize_logging_from_config(minimal_config)
        after = len(logging.getLogger().handlers)

        assert before == after


class TestGetLogger:
    """Tests for configured logger retrieval."""

    # ---- Nominal Case Tests
    def test_root_logger_access(self, minimal_config: dict) -> None:
        initialize_logging_from_config(minimal_config)

        assert get_logger('root') is logging.getLogger()

    # ---- Negative Case Tests
    def test_get_logger_before_init(self) -> None:
        with pytest.raises(RuntimeError):
            get_logger('test_logger')

    # ---- Negative Case Tests
    def test_invalid_logger_names(self, minimal_config: dict) -> None:
        initialize_logging_from_config(minimal_config)

        with pytest.raises(ValueError):
            get_logger('')
        with pytest.raises(ValueError):
            get_logger(None)  # type: ignore[arg-type]

    # ---- Negative Case Tests
    def test_unregistered_logger_rejected(self, minimal_config: dict) -> None:
        initialize_logging_from_config(minimal_config)

        with pytest.raises(ValueError, match="not registered"):
            get_logger('ghost')

    # ---- Negative Case Tests
    def test_logger_without_handlers_and_no_propagation(self) -> None:
        config = {
            'settings_version': '0.0.1',
            'app': {'environment': 'test', 'logger': 'default'},
            'logging': {
                'version': 1,
                'disable_existing_loggers': False,
                'formatters': {
                    'default': {'format': '%(message)s'},
                },
                'handlers': {
                    'null': {
                        'class': 'logging.NullHandler',
                        'formatter': 'default',
                        'level': 'NOTSET',
                    },
                },
                'loggers': {
                    'default': {
                        'handlers': ['null'],
                        'level': 'INFO',
                        'propagate': False,
                    },
                    'bad': {
                        'handlers': [],
                        'level': 'INFO',
                        'propagate': False,
                    },
                },
                'filters': {},
                'root': {'level': 'WARNING', 'handlers': []},
            },
            'integrations': {},
            'packages_groups': {},
        }

        initialize_logging_from_config(config)

        with pytest.raises(ValueError, match='not effectively configured'):
            get_logger('bad')

    # ---- Edge Case Tests
    def test_logger_propagates_but_root_has_no_handlers(self) -> None:
        config = {
            'settings_version': '0.0.1',
            'app': {'environment': 'test', 'logger': 'default'},
            'logging': {
                'version': 1,
                'disable_existing_loggers': False,
                'formatters': {
                    'default': {'format': '%(message)s'},
                },
                'handlers': {
                    'null': {
                        'class': 'logging.NullHandler',
                        'formatter': 'default',
                        'level': 'NOTSET',
                    },
                },
                'loggers': {
                    'default': {
                        'handlers': ['null'],
                        'level': 'INFO',
                        'propagate': False,
                    },
                    'test': {
                        'handlers': [],
                        'level': 'INFO',
                        'propagate': True,
                    },
                },
                'filters': {},
                'root': {'level': 'WARNING', 'handlers': []},
            },
            'integrations': {},
            'packages_groups': {},
        }

        initialize_logging_from_config(config)

        with pytest.raises(ValueError, match='not effectively configured'):
            get_logger('test')


class TestLoggingConfiguration:
    """Tests for logger configuration side effects."""

    # ---- Nominal Case Tests
    def test_levels_are_normalized(self, minimal_config: dict) -> None:
        initialize_logging_from_config(minimal_config)

        configured_logger = get_logger('test_logger')
        assert configured_logger.level == logging.INFO
        assert configured_logger.handlers[0].level == logging.INFO

    # ---- Nominal Case Tests
    def test_directory_created(self, minimal_config: dict, tmp_path: Path) -> None:
        initialize_logging_from_config(minimal_config)

        assert (tmp_path / 'logs').exists()

    # ---- Edge Case Tests
    def test_timestamped_filename(
        self,
        minimal_config: dict,
        tmp_path: Path,
    ) -> None:
        initialize_logging_from_config(minimal_config)

        assert list((tmp_path / 'logs').glob('test_*.log'))

    # ---- Nominal Case Tests
    def test_json_file_output_uses_json_extension(
        self,
        json_logging_config: dict,
        tmp_path: Path,
    ) -> None:
        initialize_logging_from_config(json_logging_config)

        log_files = list((tmp_path / 'logs').glob('json_log_*.json'))
        assert log_files
        assert not list((tmp_path / 'logs').glob('json_log_*.log'))

    # ---- Nominal Case Tests
    def test_json_file_output_writes_parseable_json_lines(
        self,
        json_logging_config: dict,
        tmp_path: Path,
    ) -> None:
        initialize_logging_from_config(json_logging_config)

        configured_logger = get_logger('json_logger')
        configured_logger.info('json-message')

        log_file = next((tmp_path / 'logs').glob('json_log_*.json'))
        record = json.loads(log_file.read_text().strip())

        assert record['message'] == 'json-message'
        assert record['levelname'] == 'INFO'
        assert record['name'] == 'json_logger'

    # ---- Edge Case Tests
    def test_json_output_keeps_console_human_readable(
        self,
        json_logging_config: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        buffer = io.StringIO()
        monkeypatch.setattr(sys, 'stdout', buffer)

        initialize_logging_from_config(json_logging_config)
        get_logger('default').info('console-message')

        assert 'console-message' in buffer.getvalue()
        assert not buffer.getvalue().strip().startswith('{')

    # ---- Nominal Case Tests
    def test_async_mode_replaces_logger_handlers_with_queue_handler(
        self,
        async_logging_config: dict,
    ) -> None:
        initialize_logging_from_config(async_logging_config)

        configured_logger = get_logger('async_logger')

        assert configured_logger.handlers
        assert all(
            isinstance(handler, QueueHandler)
            for handler in configured_logger.handlers
        )

    # ---- Nominal Case Tests
    def test_async_mode_still_writes_to_file(
        self,
        async_logging_config: dict,
        tmp_path: Path,
    ) -> None:
        initialize_logging_from_config(async_logging_config)

        configured_logger = get_logger('async_logger')
        configured_logger.info('async-message')

        deadline = time.time() + 2
        log_file = None
        while time.time() < deadline:
            matches = list((tmp_path / 'logs').glob('async_*.log'))
            if matches and 'async-message' in matches[0].read_text():
                log_file = matches[0]
                break
            time.sleep(0.05)

        assert log_file is not None
        assert 'async-message' in log_file.read_text()

    # ---- Regression Unit Tests
    def test_sync_mode_remains_non_queue_by_default(
        self,
        minimal_config: dict,
    ) -> None:
        initialize_logging_from_config(minimal_config)

        configured_logger = get_logger('test_logger')

        assert configured_logger.handlers
        assert all(
            not isinstance(handler, QueueHandler)
            for handler in configured_logger.handlers
        )


class TestFallbackBehavior:
    """Tests for fallback root handler injection."""

    # ---- Edge Case Tests
    def test_root_fallback_handlers(
        self,
        fallback_config: dict,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        buffer = io.StringIO()
        monkeypatch.setattr(sys, 'stdout', buffer)

        config_path = tmp_path / 'config.yaml'
        config_path.write_text(yaml.dump(fallback_config))

        initialize_logging(str(config_path))

        root = get_logger('root')
        root.warning('fallback')

        assert 'fallback' in buffer.getvalue()
        log_files = list((tmp_path / 'logs').glob('root_*.log'))
        assert log_files
        assert any('fallback' in path.read_text() for path in log_files)
        handler_types = {type(handler).__name__ for handler in root.handlers}
        assert 'StreamHandler' in handler_types
        assert 'RotatingFileHandler' in handler_types

    # ---- Edge Case Tests
    def test_no_fallback_if_root_has_handlers(
        self,
        fallback_config: dict,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        buffer = io.StringIO()
        monkeypatch.setattr(sys, 'stdout', buffer)

        fallback_config['logging']['root']['handlers'] = ['console']
        config_path = tmp_path / 'config.yaml'
        config_path.write_text(yaml.dump(fallback_config))

        initialize_logging(str(config_path))

        root = get_logger('root')
        root.warning('no fallback')

        assert 'no fallback' in buffer.getvalue()
        log_files = list((tmp_path / 'logs').glob('root_*.log'))
        assert not log_files or not any(
            'no fallback' in path.read_text()
            for path in log_files
        )
        handler_types = {type(handler).__name__ for handler in root.handlers}
        assert handler_types == {'StreamHandler'}


class TestLoggerIntrospection:
    """Tests for logger discovery utilities."""

    # ---- Nominal Case Tests
    def test_list_loggers_contains_registered(
        self,
        initialized_logging: dict,
    ) -> None:
        assert 'test_logger' in list_loggers()


class TestLoggerInternals:
    """Tests for selected internal helper behavior."""

    # ---- Negative Case Tests
    def test_missing_logging_section_raises(self) -> None:
        from pkg_infra.logger import LoggerConfigurator

        configurator = LoggerConfigurator()

        with pytest.raises(ValueError, match='Missing settings_version'):
            configurator.logger_setup({}, timestamp='123')

    # ---- Negative Case Tests
    def test_dictconfig_failure_propagates(
        self,
        minimal_config: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from pkg_infra.logger import LoggerConfigurator

        def boom(_: dict) -> None:
            raise ValueError('boom')

        monkeypatch.setattr('pkg_infra.logger.dictConfig', boom)

        configurator = LoggerConfigurator()

        with pytest.raises(ValueError, match='boom'):
            configurator.logger_setup(minimal_config, timestamp='123')

    # ---- Edge Case Tests
    def test_timestamp_none_generates_new(self, minimal_config: dict) -> None:
        from pkg_infra.logger import LoggerConfigurator

        configurator = LoggerConfigurator()
        configurator.logger_setup(minimal_config, timestamp=None)

        assert configurator.final_config is not None

    # ---- Regression Unit Tests
    def test_disabled_package_uses_null_handler(
        self,
        minimal_config: dict,
    ) -> None:
        from pkg_infra.logger import LoggerConfigurator

        minimal_config['integrations']['quiet_pkg'] = {
            'logging': {'enabled': False},
        }

        configurator = LoggerConfigurator()
        configurator.configure(minimal_config, timestamp='123')

        final_config = configurator.final_config
        assert final_config is not None
        assert final_config['loggers']['quiet_pkg']['handlers'] == ['null']
        assert final_config['loggers']['quiet_pkg']['propagate'] is False

    # ---- Negative Case Tests
    def test_non_mapping_config_raises_type_error(self) -> None:
        """Reject config payloads that do not resolve to mappings."""
        from pkg_infra.logger import LoggerConfigurator

        configurator = LoggerConfigurator()

        with pytest.raises(TypeError, match='must resolve to a mapping'):
            configurator.configure(['not', 'a', 'mapping'], timestamp='123')  # type: ignore[arg-type]

    # ---- Negative Case Tests
    def test_non_mapping_section_raises_type_error(self) -> None:
        """Reject required config sections that are not dictionaries."""
        from pkg_infra.logger import LoggerConfigurator

        config = {
            'settings_version': '0.0.1',
            'app': [],
            'logging': {},
            'integrations': {},
            'packages_groups': {},
        }

        with pytest.raises(TypeError, match="section 'app' must be a mapping"):
            LoggerConfigurator().configure(config, timestamp='123')

    # ---- Negative Case Tests
    def test_missing_required_sections_raise_value_error(self) -> None:
        """Reject configs that omit required logger-related sections."""
        from pkg_infra.logger import LoggerConfigurator

        config = {
            'settings_version': '0.0.1',
            'app': {'environment': 'test', 'logger': 'default'},
        }

        with pytest.raises(ValueError, match='Missing required config section'):
            LoggerConfigurator().configure(config, timestamp='123')


class TestInitializationLocking:
    """Tests for idempotent initialization guards."""

    # ---- Regression Unit Tests
    def test_initialize_logging_already_initialized(
        self,
        minimal_config: dict,
    ) -> None:
        from pkg_infra import logger as logger_module

        logger_module._logging_initialized = True

        initialize_logging_from_config(minimal_config)

    # ---- Regression Unit Tests
    def test_initialize_logging_file_already_initialized(
        self,
        minimal_config: dict,
        tmp_path: Path,
    ) -> None:
        from pkg_infra import logger as logger_module

        config_path = tmp_path / 'config.yaml'
        OmegaConf.save(minimal_config, config_path)
        logger_module._logging_initialized = True

        initialize_logging(str(config_path))

    # ---- Regression Unit Tests
    def test_initialize_logging_double_check_inside_lock(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Return early when another caller initializes logging in the lock window."""
        from pkg_infra import logger as logger_module

        class _Lock:
            def __enter__(self) -> None:
                logger_module._logging_initialized = True

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

        calls: list[str] = []
        monkeypatch.setattr(logger_module, '_logging_init_lock', _Lock())
        monkeypatch.setattr(
            logger_module,
            'ConfigLoader',
            type(
                '_Loader',
                (),
                {
                    'load_config': staticmethod(
                        lambda _path: calls.append('load') or {}
                    ),
                },
            ),
        )

        logger_module._logging_initialized = False
        logger_module.initialize_logging('config.yaml')

        assert calls == []

    # ---- Regression Unit Tests
    def test_initialize_logging_from_config_double_check_inside_lock(
        self,
        minimal_config: dict,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Return early when config initialization becomes complete inside the lock."""
        from pkg_infra import logger as logger_module

        class _Lock:
            def __enter__(self) -> None:
                logger_module._logging_initialized = True

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

        calls: list[str] = []
        monkeypatch.setattr(logger_module, '_logging_init_lock', _Lock())
        monkeypatch.setattr(
            logger_module.LoggerConfigurator,
            'configure',
            lambda self, config, timestamp=None: calls.append('configure'),
        )

        logger_module._logging_initialized = False
        logger_module.initialize_logging_from_config(minimal_config)

        assert calls == []


# =============================================================================
# ==== Function Test Cases
# =============================================================================

# Function name: _create_log_directories
# ---- Nominal Case Tests
def test_create_log_directories(tmp_path: Path) -> None:
    """Create parent directories for file handlers."""
    from pkg_infra.logger import _create_log_directories

    config = {
        'handlers': {
            'file1': {
                'class': 'logging.FileHandler',
                'filename': str(tmp_path / 'logs1' / 'a.log'),
            },
            'file2': {
                'class': 'logging.FileHandler',
                'filename': str(tmp_path / 'logs2' / 'b.log'),
            },
        },
    }

    _create_log_directories(config)

    assert (tmp_path / 'logs1').exists()
    assert (tmp_path / 'logs2').exists()


# Function name: _create_log_directories
# ---- Edge Case Tests
def test_create_log_directories_skips_non_mapping_handlers(tmp_path: Path) -> None:
    """Ignore malformed or non-file handlers while creating directories."""
    from pkg_infra.logger import _create_log_directories

    config = {
        'handlers': {
            'bad': 'not-a-mapping',
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
    }

    _create_log_directories(config)

    assert not (tmp_path / 'logs').exists()


# Function name: _patch_file_handlers_for_rotation
# ---- Nominal Case Tests
def test_patch_file_handlers_for_rotation() -> None:
    """Upgrade file handlers to rotating handlers when rotation is configured."""
    from pkg_infra.logger import _patch_file_handlers_for_rotation

    config = {
        'handlers': {
            'file': {
                'class': 'logging.FileHandler',
                'filename': 'foo.log',
                'maxBytes': 1000,
            },
            'file2': {
                'class': 'logging.FileHandler',
                'filename': 'bar.log',
                'backupCount': 2,
            },
            'plain': {
                'class': 'logging.FileHandler',
                'filename': 'baz.log',
            },
        },
    }

    _patch_file_handlers_for_rotation(config)

    assert (
        config['handlers']['file']['class']
        == 'logging.handlers.RotatingFileHandler'
    )
    assert (
        config['handlers']['file2']['class']
        == 'logging.handlers.RotatingFileHandler'
    )
    assert config['handlers']['plain']['class'] == 'logging.FileHandler'
    assert config['handlers']['file']['maxBytes'] == 1000
    assert config['handlers']['file']['backupCount'] == 5
    assert config['handlers']['file2']['maxBytes'] == 10 * 1024 * 1024
    assert config['handlers']['file2']['backupCount'] == 2


# Function name: _patch_file_handlers_for_rotation
# ---- Edge Case Tests
def test_patch_file_handlers_for_rotation_ignores_non_dict_handlers() -> None:
    """Skip malformed handlers and non-dict handler collections."""
    from pkg_infra.logger import _patch_file_handlers_for_rotation

    config = {
        'handlers': {
            'broken': 'not-a-dict',
        },
    }

    _patch_file_handlers_for_rotation(config)

    assert config['handlers']['broken'] == 'not-a-dict'


# Function name: _uppercase_levels
# ---- Nominal Case Tests
def test_uppercase_levels() -> None:
    """Normalize nested logging levels to uppercase."""
    from pkg_infra.logger import _uppercase_levels

    config = {
        'level': 'info',
        'handlers': [
            {'level': 'debug'},
            {'nested': {'level': 'warning'}},
        ],
        'loggers': {
            'foo': {'level': 'error'},
        },
    }

    _uppercase_levels(config)

    assert config['level'] == 'INFO'
    assert config['handlers'][0]['level'] == 'DEBUG'
    assert config['handlers'][1]['nested']['level'] == 'WARNING'
    assert config['loggers']['foo']['level'] == 'ERROR'


# Function name: _ensure_root_handlers
# ---- Edge Case Tests
def test_ensure_root_handlers_injects_and_skips() -> None:
    """Inject fallback root handlers only when none are configured."""
    from pkg_infra.logger import _ensure_root_handlers

    config = {
        'handlers': {'console': {}, 'file': {}},
        'root': {},
    }

    _ensure_root_handlers(config)
    assert set(config['root']['handlers']) == {'console', 'file'}

    config_with_handlers = {
        'handlers': {'console': {}, 'file': {}},
        'root': {'handlers': ['console']},
    }

    _ensure_root_handlers(config_with_handlers)
    assert config_with_handlers['root']['handlers'] == ['console']


# Function name: _ensure_root_handlers
# ---- Edge Case Tests
def test_ensure_root_handlers_ignores_invalid_root_shape() -> None:
    """Return early when handlers or root are not dictionaries."""
    from pkg_infra.logger import _ensure_root_handlers

    config = {
        'handlers': [],
        'root': [],
    }

    _ensure_root_handlers(config)

    assert config['handlers'] == []
    assert config['root'] == []


# Function name: _recursive_update
# ---- Edge Case Tests
def test_recursive_update_nested_filenames() -> None:
    """Update all nested filename keys with the provided timestamp."""
    from pkg_infra.logger import _recursive_update

    config = {
        'handlers': {
            'file': {
                'class': 'logging.FileHandler',
                'filename': 'a.log',
            },
        },
        'nested': [
            {'filename': 'b.log'},
            [{'filename': 'c.log'}],
        ],
    }

    _recursive_update(config, timestamp='123')

    assert 'a_123.log' in str(config)
    assert 'b_123.log' in str(config)
    assert 'c_123.log' in str(config)


# Function name: _update_single_filename
# ---- Nominal Case Tests
def test_update_single_filename() -> None:
    """Append timestamps while preserving the original extension."""
    from pkg_infra.logger import _update_single_filename

    assert _update_single_filename('foo.log', '123') == 'foo_123.log'
    assert _update_single_filename('bar', '456') == 'bar_456'
    assert _update_single_filename('baz.txt', '789') == 'baz_789.txt'


# Function name: get_timestamp_now
# ---- Nominal Case Tests
def test_get_timestamp_now_uses_utc_z_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return UTC timestamps with an explicit trailing Z marker."""
    import pkg_infra.utils as utils_module

    class FrozenDateTime(datetime):
        """Frozen datetime class for deterministic UTC timestamp tests."""

        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            return cls(2026, 3, 31, 12, 30, 36, tzinfo=timezone.utc)

    monkeypatch.setattr(utils_module.datetime, 'datetime', FrozenDateTime)

    assert utils_module.get_timestamp_now() == '20260331T123036Z'


# Function name: get_logger
# ---- Edge Case Tests
def test_get_logger_uses_root_fallback_when_propagation_is_enabled() -> None:
    """Return a logger that relies on the configured root logger."""
    from pkg_infra import logger as logger_module

    root_logger = logging.getLogger()
    root_handler = logging.StreamHandler(io.StringIO())
    root_logger.addHandler(root_handler)

    try:
        configured_logger = logging.getLogger('propagating_logger')
        configured_logger.handlers.clear()
        configured_logger.propagate = True
        logger_module._logging_initialized = True

        assert get_logger('propagating_logger') is configured_logger
    finally:
        root_logger.removeHandler(root_handler)


# Function name: _normalize_base_logging_config
# ---- Negative Case Tests
def test_normalize_base_logging_config_rejects_unknown_formatter() -> None:
    """Fail when a handler references a missing formatter."""
    from pkg_infra.logger import _normalize_base_logging_config

    with pytest.raises(ValueError, match='unknown formatter'):
        _normalize_base_logging_config(
            {
                'version': 1,
                'disable_existing_loggers': False,
                'formatters': {},
                'handlers': {
                    'file': {
                        'class': 'logging.FileHandler',
                        'formatter': 'missing',
                        'filename': 'app.log',
                        'level': 'INFO',
                    },
                },
                'loggers': {},
                'filters': {},
                'root': {'level': 'WARNING', 'handlers': []},
            },
        )


# Function name: _normalize_base_logging_config
# ---- Negative Case Tests
def test_normalize_base_logging_config_rejects_unknown_filter() -> None:
    """Fail when a handler references a missing filter."""
    from pkg_infra.logger import _normalize_base_logging_config

    with pytest.raises(ValueError, match='unknown filter'):
        _normalize_base_logging_config(
            {
                'version': 1,
                'disable_existing_loggers': False,
                'formatters': {'default': {'format': '%(message)s'}},
                'handlers': {
                    'file': {
                        'class': 'logging.FileHandler',
                        'formatter': 'default',
                        'filename': 'app.log',
                        'filters': ['missing'],
                        'level': 'INFO',
                    },
                },
                'loggers': {},
                'filters': {},
                'root': {'level': 'WARNING', 'handlers': []},
            },
        )


# Function name: _normalize_base_logging_config
# ---- Negative Case Tests
def test_normalize_base_logging_config_rejects_unknown_logger_handler() -> None:
    """Fail when a logger references an undefined handler."""
    from pkg_infra.logger import _normalize_base_logging_config

    with pytest.raises(ValueError, match='unknown handler'):
        _normalize_base_logging_config(
            {
                'version': 1,
                'disable_existing_loggers': False,
                'formatters': {'default': {'format': '%(message)s'}},
                'handlers': {},
                'loggers': {
                    'demo': {
                        'handlers': ['missing'],
                        'level': 'INFO',
                        'propagate': False,
                    },
                },
                'filters': {},
                'root': {'level': 'WARNING', 'handlers': []},
            },
        )


# Function name: _normalize_base_logging_config
# ---- Negative Case Tests
def test_normalize_base_logging_config_rejects_unknown_root_handler() -> None:
    """Fail when the root logger references an undefined handler."""
    from pkg_infra.logger import _normalize_base_logging_config

    with pytest.raises(ValueError, match='Root logger references unknown handler'):
        _normalize_base_logging_config(
            {
                'version': 1,
                'disable_existing_loggers': False,
                'formatters': {},
                'handlers': {},
                'loggers': {},
                'filters': {},
                'root': {'level': 'WARNING', 'handlers': ['missing']},
            },
        )


# Function name: _normalize_base_logging_config
# ---- Negative Case Tests
def test_normalize_base_logging_config_rejects_unknown_top_level_key() -> None:
    """Fail when unsupported logging keys are present."""
    from pkg_infra.logger import _normalize_base_logging_config

    with pytest.raises(ValueError, match='Unknown key\\(s\\) in logging config'):
        _normalize_base_logging_config(
            {
                'version': 1,
                'disable_existing_loggers': False,
                'formatters': {},
                'handlers': {},
                'loggers': {},
                'filters': {},
                'root': {'level': 'WARNING', 'handlers': []},
                'unexpected': True,
            },
        )


# Function name: _validate_handler_filters
# ---- Negative Case Tests
def test_validate_handler_filters_rejects_non_list_filters() -> None:
    """Require handler filters to be lists."""
    from pkg_infra.logger import _validate_handler_filters

    with pytest.raises(TypeError, match='filters must be a list'):
        _validate_handler_filters(
            handlers={'demo': {'filters': 'not-a-list'}},
            filters={},
        )


# Function name: _validate_logger_handlers
# ---- Negative Case Tests
def test_validate_logger_handlers_rejects_non_list_handlers() -> None:
    """Require logger handlers to be lists."""
    from pkg_infra.logger import _validate_logger_handlers

    with pytest.raises(TypeError, match='handlers must be a list'):
        _validate_logger_handlers(
            loggers={'demo': {'handlers': 'not-a-list'}},
            handlers={},
        )


# Function name: _validate_root_handlers
# ---- Negative Case Tests
def test_validate_root_handlers_rejects_non_list_handlers() -> None:
    """Require root handlers to be lists."""
    from pkg_infra.logger import _validate_root_handlers

    with pytest.raises(TypeError, match='Root logger handlers must be a list'):
        _validate_root_handlers(
            root={'handlers': 'not-a-list'},
            handlers={},
        )


# Function name: _build_group_index
# ---- Negative Case Tests
def test_build_group_index_rejects_non_list_packages() -> None:
    """Require package groups to declare package names as lists."""
    from pkg_infra.logger import _build_group_index

    with pytest.raises(TypeError, match='packages must be a list'):
        _build_group_index({'group': {'packages': 'pkg_a'}})


# Function name: _build_group_index
# ---- Negative Case Tests
def test_build_group_index_rejects_duplicate_membership() -> None:
    """Reject packages that belong to more than one group."""
    from pkg_infra.logger import _build_group_index

    with pytest.raises(ValueError, match='is in multiple groups'):
        _build_group_index(
            {
                'group_a': {'packages': ['pkg_a']},
                'group_b': {'packages': ['pkg_a']},
            },
        )


# Function name: _merge_loggers_into_base_config
# ---- Negative Case Tests
def test_merge_loggers_into_base_config_requires_mapping_loggers() -> None:
    """Reject malformed loggers sections before merging generated entries."""
    from pkg_infra.logger import _merge_loggers_into_base_config

    with pytest.raises(TypeError, match='"loggers" section must be a mapping'):
        _merge_loggers_into_base_config(
            base_logging_config={'loggers': []},
            logger_entries={'demo': {'level': 'INFO'}},
        )


# Function name: _validate_final_logging_config
# ---- Negative Case Tests
def test_validate_final_logging_config_requires_handlers() -> None:
    """Reject final configs that omit handlers entirely."""
    from pkg_infra.logger import _validate_final_logging_config

    with pytest.raises(ValueError, match='No handlers defined'):
        _validate_final_logging_config({'loggers': {}})


# Function name: _validate_final_logging_config
# ---- Negative Case Tests
def test_validate_final_logging_config_requires_loggers() -> None:
    """Reject final configs that omit loggers entirely."""
    from pkg_infra.logger import _validate_final_logging_config

    with pytest.raises(ValueError, match='No loggers defined'):
        _validate_final_logging_config({'handlers': {}})
