#!/usr/bin/env python3
"""
Standalone launcher for the Cisco GPS NETCONF tool.

Usage:
    python run_cisco_gps_netconf.py -H 192.168.2.191 -u cisco -p cisco
    python -m cisco_gps_netconf -H 192.168.2.191 -u cisco -p cisco  (after pip install -e .)
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from cisco_gps_netconf.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
