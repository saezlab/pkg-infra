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

"""
Session handler, configuration, and logging handler for Saezlab packages and applications.
"""

import datetime
import logging

# Generate a single timestamp for log files
LOG_TIMESTAMP = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
__log_timestamp__ = LOG_TIMESTAMP

# Configure the root logger with the timestamp
from pkg_infra.logger import get_root_logger_configured
get_root_logger_configured(timestamp=LOG_TIMESTAMP)


# Public API

from ._metadata import __author__, __version__
from .session import get_session

__all__ = [
    'get_session',
    '__version__',
    '__author__'
]

# Log import for debugging
logging.info(f"Importing {__name__}")
