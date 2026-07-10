#!/usr/bin/env python

#
# This file is part of the `pkg_infra` Python module
#
# Copyright 2025
# Heidelberg University Hospital
#
# File author(s): Edwin Carreño (ecarrenolozano@gmail.com)
#
# Distributed under the MIT license
# See the file `LICENSE` or read a copy at
# https://opensource.org/license/mit
#


"""Session handler, configuration, and logging handler for Saezlab packages and applications."""

from pathlib import Path

from pkg_infra._metadata import __author__, __version__


def get_session(
    workspace: str | Path,
    include_location: bool = False,
    config_path: str | Path | None = None,
) -> object:
    """Lazily import and return ``pkg_infra.session.get_session``.

    Args:
        workspace:
            Path to the workspace directory.
        include_location:
            Whether to allow lazy geolocation lookup.
        config_path:
            Optional path to a custom configuration file to merge.

    Returns:
        Session: The current session instance.
    """
    from pkg_infra.session import get_session as _get_session

    return _get_session(
        workspace=workspace,
        include_location=include_location,
        config_path=config_path,
    )


def logfile() -> Path | None:
    """Return the current active log file, or ``None`` if none is configured.

    Thin re-export of :func:`pkg_infra.logger.logfile`.
    """
    from pkg_infra.logger import logfile as _logfile

    return _logfile()


def log_files() -> list[Path]:
    """Return every active log-file path.

    Thin re-export of :func:`pkg_infra.logger.log_files`.
    """
    from pkg_infra.logger import log_files as _log_files

    return _log_files()


def open_log(
    path: str | Path | None = None,
    pager: str | None = None,
) -> Path | None:
    """Open a log file in a terminal pager.

    Thin re-export of :func:`pkg_infra.logger.open_log`.
    """
    from pkg_infra.logger import open_log as _open_log

    return _open_log(path=path, pager=pager)


__all__ = [
    'get_session',
    'logfile',
    'log_files',
    'open_log',
    '__version__',
    '__author__',
]
