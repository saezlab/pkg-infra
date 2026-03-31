"""Demonstrate thread-safe singleton session initialization.

This script widens the configuration-loading window by monkeypatching
``pkg_infra.session._get_configuration`` to sleep. It then launches two threads
that call ``get_session()`` at the same time and reports whether the singleton
was initialized more than once.

Usage:
    .venv/bin/python sandbox/scripts/race_get_session_demo.py
"""

from __future__ import annotations

import logging
import threading
import time

import pkg_infra.session as session_module


def run_trial() -> tuple[int, int]:
    """Run one concurrent initialization attempt."""
    session_module.reset_session()
    results: list[int] = []
    counter = {'init_calls': 0}
    barrier = threading.Barrier(2)

    original_get_configuration = session_module._get_configuration

    def slow_get_configuration() -> object:
        counter['init_calls'] += 1
        time.sleep(0.2)
        return original_get_configuration()

    session_module._get_configuration = slow_get_configuration

    try:
        def worker() -> None:
            barrier.wait()
            session = session_module.get_session('.', include_location=False)
            results.append(id(session))

        first = threading.Thread(target=worker, name='session-worker-1')
        second = threading.Thread(target=worker, name='session-worker-2')
        first.start()
        second.start()
        first.join()
        second.join()
    finally:
        session_module._get_configuration = original_get_configuration
        session_module.reset_session()

    return counter['init_calls'], len(set(results))


def main() -> None:
    """Execute multiple trials and print a concise concurrency summary."""
    trials = 20
    multiple_init_calls = 0
    multiple_session_objects = 0

    logging.disable(logging.CRITICAL)
    try:
        for _ in range(trials):
            init_calls, unique_sessions = run_trial()
            if init_calls > 1:
                multiple_init_calls += 1
            if unique_sessions > 1:
                multiple_session_objects += 1
    finally:
        logging.disable(logging.NOTSET)

    print(f'Trials: {trials}')
    print(f'Trials with >1 configuration load call: {multiple_init_calls}')
    print(f'Trials with >1 unique session object: {multiple_session_objects}')
    print('Expected result with the current implementation: both counters stay at 0.')


if __name__ == '__main__':
    main()
