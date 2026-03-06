## Description

The `_metadata.py` file defines the package-level metadata for the `pkg_infra` distribution. It exposes information such as the package version, author details, and license in a central place so that other parts of the codebase, packaging tooling, and documentation can reliably reference this information.

### Main Components

- **Package metadata attributes:**
  Module-level values (for example, version, author(s), and license) that can be imported by other modules and external tools to report or validate the package’s identity and release information.

---

::: pkg_infra._metadata
