#!/usr/bin/env python

#
# This file is part of the `saezlab_core` Python module
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

from .logger import get_logger
from .session_bkp import Session

__all__ = ['get_logger', 'Session']

"""This is session handler, configuration and logging handler for Saezlab packages and applications."""

__all__ = [
    '__version__',
    '__author__',
]

# from ._metadata import __author__, __version__
