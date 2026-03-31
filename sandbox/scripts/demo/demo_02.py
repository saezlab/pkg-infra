"""Demo 02: inspect package-scoped configuration propagation.

Usage:
    .venv/bin/python sandbox/scripts/demo/demo_02.py
"""

from __future__ import annotations

from pathlib import Path

from pkg_infra import get_session
from pkg_infra.session import reset_session


CONFIG_PATH = Path('sandbox/scripts/demo/config.yaml')


def main() -> None:
    """Show how ``Session.get_conf`` returns only integration settings."""
    reset_session()
    session = get_session('sandbox/scripts/demo', config_path=CONFIG_PATH)
    logger = session.session_logger
    if logger is None:
        raise RuntimeError('Session logger is not initialized.')

    logger.info('Demo 02 started')

    ontograph = session.get_conf('ontograph')
    corneto = session.get_conf('corneto')
    omnipath = session.get_conf('omnipath')

    print('Resolved integration settings')
    print(f'  ontograph: {ontograph}')
    print(f'  corneto: {corneto}')
    print(f'  omnipath: {omnipath}')
    print()
    print('Notes')
    print('  - Only integration.settings are returned.')
    print('  - Missing packages resolve to an empty dict.')
    print('  - Group logging configuration is not leaked into package settings.')


if __name__ == '__main__':
    main()
