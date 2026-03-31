"""Demo 03: structured JSON file logging for downstream analysis tools.

Usage:
    .venv/bin/python sandbox/scripts/demo/demo_03.py
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

from pkg_infra import get_session
from pkg_infra.session import reset_session


LOG_DIR = Path('sandbox/scripts/demo/logs')


def main() -> None:
    """Write JSON logs and print one parsed record."""
    reset_session()
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.yaml',
        delete=False,
        encoding='utf-8',
    ) as handle:
        handle.write(
            '\n'.join([
                'logging:',
                '  file_output_format: json',
                '  handlers:',
                '    file:',
                '      filename: sandbox/scripts/demo/logs/structured_demo.log',
            ]),
        )
        override_path = Path(handle.name)

    session = get_session(
        'sandbox/scripts/demo',
        config_path=override_path,
    )
    logger = session.session_logger
    if logger is None:
        raise RuntimeError('Session logger is not initialized.')

    logger.info('Structured logging demo started')
    logger.warning('This record can be parsed by log analysis tooling')

    json_files = sorted(LOG_DIR.glob('structured_demo_*.json'))
    if not json_files:
        raise RuntimeError('No JSON log file was created.')

    log_file = json_files[-1]
    last_record = json.loads(log_file.read_text(encoding='utf-8').splitlines()[-1])

    print(f'JSON log file: {log_file}')
    print(f'Parsed keys: {sorted(last_record)}')
    print(f'Message: {last_record["message"]}')


if __name__ == '__main__':
    main()
