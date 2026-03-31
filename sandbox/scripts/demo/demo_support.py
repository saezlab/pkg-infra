"""Support helpers for sandbox demos."""

from __future__ import annotations

import logging
import time


class SlowFileHandler(logging.FileHandler):
    """File handler that sleeps on each emit to simulate slow I/O."""

    def __init__(
        self,
        filename: str,
        mode: str = 'a',
        encoding: str | None = None,
        delay: bool = False,
        delay_seconds: float = 0.005,
    ) -> None:
        super().__init__(
            filename=filename,
            mode=mode,
            encoding=encoding,
            delay=delay,
        )
        self.delay_seconds = float(delay_seconds)

    def emit(self, record: logging.LogRecord) -> None:
        """Delay emission to make the benefit of async logging visible."""
        time.sleep(self.delay_seconds)
        super().emit(record)
