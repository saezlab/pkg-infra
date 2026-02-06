import getpass
import json
import logging
import socket
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.request import urlopen


from saezlab_core.config_test import ConfigLoader

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())

@dataclass(frozen=True)
class Session:
    id: str
    user: str
    workspace: Path
    started_at_utc: str
    started_at_local: str
    timezone: str | None
    location: str | None
    hostname: str
    config: None

    def log(self, logger: logging.Logger = _logger) -> None:
        logger.info("Session data: ")
        for attribute in self.__annotations__.keys():
            logger.info("%s: %s", attribute, getattr(self, attribute))

_session: Session | None = None


def _lookup_location(timeout: float = 2.0) -> str | None:
    """Best-effort geolocation using a public IP lookup."""
    _logger.debug("Resolving location via ipinfo.io")
    try:
        with urlopen("https://ipinfo.io/json", timeout=timeout) as response:
            data = json.load(response)
            city = data.get("city")
            region = data.get("region")
            country = data.get("country")
            parts = [p for p in (city, region, country) if p]
            location = ", ".join(parts) if parts else None
            _logger.info("Resolved location: %s", location)
            return location
    except (URLError, ValueError):
        _logger.warning("Location lookup failed", exc_info=True)
        return None

def get_session(workspace: str | Path, include_location: bool = True) -> Session:
    """Return a singleton Session for this process."""
    global _session
    _logger.debug("Requesting session for workspace: %s", workspace)
    if _session is None:
        now_utc = datetime.now(timezone.utc)
        now_local = datetime.now().astimezone()
        location = _lookup_location() if include_location else None
        _logger.info("Creating new session")
        _session = Session(
            id=str(uuid.uuid4()),
            user=getpass.getuser(),
            workspace=Path(workspace).expanduser().resolve(),
            started_at_utc=now_utc.isoformat().replace("+00:00", "Z"),
            started_at_local=now_local.isoformat(),
            timezone=now_local.tzname(),
            location=location,
            hostname=socket.gethostname(),
            config=ConfigLoader.load_config()
        )
    else:
        _logger.debug("Reusing existing session")
    return _session


__all__ = ["Session", "get_session"]
