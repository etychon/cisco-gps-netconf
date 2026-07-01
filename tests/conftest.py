"""Pytest configuration: prefer the src package over the root launcher script."""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
_src_str = str(_SRC)
if _src_str not in sys.path:
    sys.path.insert(0, _src_str)

# Drop root launcher module if it was imported before the package.
if "cisco_gps_netconf" in sys.modules:
    mod = sys.modules["cisco_gps_netconf"]
    mod_file = getattr(mod, "__file__", "") or ""
    if mod_file.endswith("cisco_gps_netconf.py"):
        del sys.modules["cisco_gps_netconf"]
