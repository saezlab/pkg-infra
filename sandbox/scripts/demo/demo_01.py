"""Demo 01: basic session creation and application logging.

Usage:
    .venv/bin/python sandbox/scripts/demo/demo_01.py
"""

from __future__ import annotations

from pathlib import Path

from pkg_infra import get_session
from pkg_infra.session import reset_session


CONFIG_PATH = Path('sandbox/scripts/demo/config.yaml')
LOG_DIR = CONFIG_PATH.parent / 'logs'


def main() -> None:
    """Create a session, log a few messages, and show the resulting runtime."""
    reset_session()
    session = get_session('sandbox/scripts/demo', config_path=CONFIG_PATH)
    logger = session.session_logger
    if logger is None:
        raise RuntimeError('Session logger is not initialized.')

    logger.info('Demo 01 started')
    logger.info('Session id: %s', session.id)
    logger.info('Workspace: %s', session.workspace)
    logger.warning('Warnings go to both console and file handlers.')

    print('Session summary')
    print(f'  hostname: {session.hostname}')
    print(f'  workspace: {session.workspace}')
    print(f'  logger: {logger.name}')
    print(f'  config path: {CONFIG_PATH}')

    log_files = sorted(path.name for path in LOG_DIR.glob('demo_*.log'))
    print(f'  log files: {log_files}')


if __name__ == '__main__':
    main()
