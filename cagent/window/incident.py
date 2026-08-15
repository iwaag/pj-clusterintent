#!/usr/bin/env python3
"""CLI shim: `uv run cagent/window/incident.py ...` keeps working.

The implementation moved into the package (`cagent_api.incident`) when the
window stopped having a shell to run a script from — its incident tools call
those functions directly now. This file stays because the command is written
down in the developer notes and in window/GUIDE.md, and because a human
reading incidents back should not have to know it moved.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cagent_api.incident import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
