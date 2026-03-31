#!/bin/bash
set -euo pipefail

TMPDIR=$(mktemp -d)
echo "$TMPDIR"
cd "$TMPDIR"

cat > log_rotate_test.py <<'PY'
from pathlib import Path

from pkg_infra.logger import get_logger, initialize_logging_from_config


config = {
    "settings_version": "0.0.1",
    "app": {
        "environment": "test",
        "logger": "default",
    },
    "logging": {
        "version": 1,
        "disable_existing_loggers": False,
        "file_output_format": "text",
        "formatters": {
            "simple": {"format": "%(levelname)s | %(message)s"},
        },
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "test.log",
                "maxBytes": 1024,
                "backupCount": 2,
                "formatter": "simple",
                "level": "INFO",
            },
            "null": {
                "class": "logging.NullHandler",
                "formatter": "simple",
                "level": "NOTSET",
            },
        },
        "loggers": {
            "default": {
                "level": "INFO",
                "handlers": ["file"],
                "propagate": False,
            },
        },
        "filters": {},
        "root": {
            "level": "INFO",
            "handlers": ["file"],
        },
    },
    "integrations": {},
    "packages_groups": {},
}

initialize_logging_from_config(config)
logger = get_logger("default")

results = []
results.append((logger.level == 20, f"Logger level is INFO (20): {logger.level == 20}"))
results.append((logger.name == "default", f"Logger is default: {logger.name == 'default'}"))

for index in range(2000):
    logger.debug("DEBUG line %s", index)
    logger.info("INFO line %s", index)
    logger.warning("WARNING line %s", index)

log_files = sorted(Path(".").glob("test_*.log"))
results.append((bool(log_files), f"Timestamped log files created: {bool(log_files)}"))

found_debug = False
found_info = False
found_warning = False
for path in log_files:
    content = path.read_text(encoding="utf-8")
    if "DEBUG line" in content:
        found_debug = True
    if "INFO line" in content:
        found_info = True
    if "WARNING line" in content:
        found_warning = True

results.append((not found_debug, f"DEBUG messages filtered: {not found_debug}"))
results.append((found_info, f"INFO messages present: {found_info}"))
results.append((found_warning, f"WARNING messages present: {found_warning}"))

print("\nACCEPTANCE CRITERIA RESULTS:")
for passed, message in results:
    print(f"[{'PASS' if passed else 'FAIL'}] {message}")
PY

python3 log_rotate_test.py
ls -lh test_*.log
