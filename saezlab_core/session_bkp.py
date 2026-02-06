from .config import ConfigLoader
from .logger import get_logger, setup_logging, stop_async_listener

__all__ = [
    'Session',
]


class Session:
    """Central session manager for config and logging.

    Ensures singleton initialization and global access to config and loggers.
    """

    _initialized = False
    _config = None

    @classmethod
    def stop_logging(cls) -> None:
        """Stop the async logging listener (if any) to flush all logs."""
        stop_async_listener()

    @classmethod
    def initialize(cls, config_path: str) -> None:
        """Initialize session with config and logging. Only runs once."""
        if cls._initialized:
            return
        cls._config = ConfigLoader.load(config_path)
        setup_logging(cls._config.get('logging', {}))
        cls._initialized = True

    @classmethod
    def get_config(cls) -> object:
        """Get the loaded config (DictConfig)."""
        return cls._config

    @staticmethod
    def get_logger(name: str) -> object:
        """Get a logger for a given module/component."""
        return get_logger(name)

    @classmethod
    def reset(cls) -> None:
        """Reset the session (for testing or re-initialization)."""
        cls._initialized = False
        cls._config = None
