# Cisco GPS NETCONF Retrieval Tool

Retrieve GPS coordinates and cellular radio metrics from Cisco IOS XE routers using NETCONF — no SSH/CLI fallback required.

Tested on a **Cisco IR1835** (IOS XE 26.02) with three independent GPS sources: platform GNSS/GPS/DR module and two cellular interfaces.

## Features

- **Multi-source GPS** — returns every available GPS source in one run (platform GNSS module + cellular interfaces)
- **NETCONF-only** — uses IOS XE operational YANG models; no CLI or SSH dependency
- **Correct YANG models** for IR1800/IR1835-class devices:
  - `Cisco-IOS-XE-gnss-dr-oper` — platform GNSS/GPS/DR (`show platform hardware gps detail`)
  - `Cisco-IOS-XE-cellwan-oper` — cellular GPS and radio (`cellwan-gps`, `cellwan-radio`)
  - `Cisco-IOS-XE-gnss-oper` — slot-based GNSS (queried when present; not populated on IR1835)
- **DMS parsing** — converts cellular GPS coordinates from NETCONF DMS strings to decimal degrees
- **Cellular radio metrics** — optional `--cellular` mode for RSSI, RSRP, band, PCI, etc.
- **Multiple output formats** — decimal degrees, DMS, map links (Google Maps, OpenStreetMap, Bing Maps)
- **JSON export** — save structured results for automation pipelines
- **Interface filtering** — limit cellular sources with `--interfaces`

## Requirements

- Python 3.9+ (3.7 declared in packaging; CI tests 3.9+)
- Cisco router with NETCONF enabled and GPS configured
- Network access to TCP port **830** (default NETCONF over SSH)

## Installation

### Option A — Run without installing (quick start)

```bash
git clone https://github.com/etychon/cisco-gps-netconf.git
cd cisco-gps-netconf
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-standalone.txt
python run_cisco_gps_netconf.py --help
```

### Option B — Install as a package

```bash
git clone https://github.com/etychon/cisco-gps-netconf.git
cd cisco-gps-netconf
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cisco-gps-netconf --help
# or
python -m cisco_gps_netconf --help
```

## Router Prerequisites

### Enable NETCONF (IOS XE)

```
configure terminal
netconf-yang
netconf ssh
username netconf_user privilege 15 secret <password>
ip ssh version 2
end
```

Verify: `show netconf-yang statistics`

### GPS on IR1835 (example)

**Platform GNSS/GPS/DR module** (IRM-GNSS):

```
configure terminal
gps enable
end
```

Verify: `show platform hardware gps detail`

**Cellular GPS** (per modem):

```
configure terminal
interface Cellular0/4/0
 gps enable
 gps mode standalone
exit
interface Cellular0/5/0
 gps enable
 gps mode mbased
end
```

Verify: `show cellular 0/4/0 gps` and `show cellular 0/5/0 gps`

## Usage

### CLI reference

```
usage: cisco-gps-netconf [-h] -H HOST -u USERNAME -p PASSWORD [-P PORT]
                         [-o OUTPUT] [-t TIMEOUT] [-v] [--cellular]
                         [--interfaces INTERFACES] [--version]
```

| Flag | Description |
|------|-------------|
| `-H`, `--host` | Router IP or hostname (required) |
| `-u`, `--username` | NETCONF username (required) |
| `-p`, `--password` | NETCONF password (required) |
| `-P`, `--port` | NETCONF port (default: 830) |
| `-o`, `--output` | Write JSON results to file |
| `-t`, `--timeout` | Connection timeout in seconds (default: 30) |
| `--cellular` | Include per-interface cellular radio metrics |
| `--interfaces` | Comma-separated cellular interfaces to include |
| `-v`, `--verbose` | Print raw result dict after formatted output |

### Examples (IR1835 lab device)

All GPS sources (GNSS module + all cellular interfaces discovered via NETCONF):

```bash
python run_cisco_gps_netconf.py -H 192.168.2.191 -u netconf_user -p '<password>'
```

Limit to two cellular modems (platform GNSS is always included):

```bash
python run_cisco_gps_netconf.py -H 192.168.2.191 -u netconf_user -p '<password>' \
  --interfaces Cellular0/4/0,Cellular0/5/0
```

GPS + cellular radio metrics, save JSON:

```bash
python run_cisco_gps_netconf.py -H 192.168.2.191 -u netconf_user -p '<password>' \
  --interfaces Cellular0/4/0,Cellular0/5/0 --cellular -o gps_report.json
```

### Sample output — all GPS sources

Captured from a Cisco **IR1835** running IOS XE **26.02** with three active fixes:

```
Connecting to 192.168.2.191:830...
NETCONF connection established successfully
Querying GNSS/GPS/DR module (platform hardware GPS)...
  Found coordinates for GNSS_GPS_DR
Querying Cellular GPS...
  Found coordinates for Cellular0/4/0
  Found coordinates for Cellular0/5/0
Querying GNSS slot module (gnss-oper)...
  Cisco-IOS-XE-gnss-oper: no location fix (on IR1835 the platform GNSS module is exposed via gnss-dr-oper)
============================================================
GPS COORDINATES RETRIEVED
Sources: 3
============================================================

Source: GNSS_GPS_DR
----------------------------------------
Type: platform_hardware_gps
YANG: Cisco-IOS-XE-gnss-dr-oper
CLI equivalent: show platform hardware gps detail
Decimal Degrees:
  Latitude:  50.612892°
  Longitude: 5.585948°
Degrees, Minutes, Seconds:
  Latitude:  50° 36' 46.41" N
  Longitude: 5° 35' 9.41" E
Map Links:
  Google Maps: https://www.google.com/maps?q=50.612892,5.585948
  ...
Timestamp: 2026-07-01T09:00:19+00:00
GPS Status: gps-dr-state-enabled

Source: Cellular0/4/0
----------------------------------------
Type: cellular
YANG: Cisco-IOS-XE-cellwan-oper
Decimal Degrees:
  Latitude:  50.612463°
  Longitude: 5.586687°
Degrees, Minutes, Seconds:
  Latitude:  50° 36' 44.868" N
  Longitude: 5° 35' 12.0744" E
Map Links:
  Google Maps: https://www.google.com/maps?q=50.612463,5.586687
  ...
Timestamp: 2026-07-01T09:02:50+00:00
GPS Status: gps-state-enabled
GPS Mode: gps-mode-standalone

Source: Cellular0/5/0
----------------------------------------
Type: cellular
YANG: Cisco-IOS-XE-cellwan-oper
Decimal Degrees:
  Latitude:  50.612531°
  Longitude: 5.586677°
...
GPS Status: gps-state-enabled
GPS Mode: gps-mode-mbased
============================================================
```

### Sample output — `--cellular` (radio metrics)

```
CELLULAR RADIO INFORMATION (1 interfaces):
------------------------------

Interface: Cellular0/5/0
  Power Mode: radio-power-mode-online
  LTE Band: 7
  LTE Bandwidth: bandwidth-15-mhz
  LTE Rx Channel (PCC): 3175
  LTE Tx Channel (PCC): 21175
  RSSI: -71 dBm
  RSRP: -98 dBm
  RSRQ: -9 dB
  SNR: 11.2 dB
  Physical Cell ID: 114
  RAT Preference: lte-radio-tech-auto
  RAT Selected: system-mode-lte-fdd
```

### Python API

```python
from cisco_gps_netconf import CiscoGPSRetriever

retriever = CiscoGPSRetriever(
    host="192.168.2.191",
    username="netconf_user",
    password="<password>",
    interfaces=["Cellular0/4/0", "Cellular0/5/0"],
)

sources = retriever.retrieve_and_display_gps(output_file="gps.json")
for source_id, data in sources.items():
    print(source_id, data["latitude"], data["longitude"], data.get("gps_status"))

# GPS + radio metrics
report = retriever.retrieve_and_display_cellular(output_file="cellular.json")
```

See also [`example_usage.py`](example_usage.py).

## How GPS sources map to NETCONF

| Source ID | Router CLI equivalent | YANG model | NETCONF container |
|-----------|----------------------|------------|-------------------|
| `GNSS_GPS_DR` | `show platform hardware gps detail` | `Cisco-IOS-XE-gnss-dr-oper` | `gnss-dr-data` |
| `Cellular0/x/y` | `show cellular 0/x/y gps` | `Cisco-IOS-XE-cellwan-oper` | `cellwan-gps` |
| `gnss_oper_slot_*` | `show gnss status` (when present) | `Cisco-IOS-XE-gnss-oper` | `gnss-data` |

On the IR1835, the IRM-GNSS module is exposed through **`gnss-dr-oper`**, not `gnss-oper`. The tool still queries `gnss-oper` for platforms where it is populated.

### Fix status values

| NETCONF state | Meaning |
|---------------|---------|
| `gps-dr-state-enabled` | Platform GNSS module has coordinates |
| `gps-state-enabled` | Cellular GPS has a fix |
| `gps-state-acquiring` | Cellular GPS still acquiring — coordinates may be stale |

## Project layout

```
cisco-gps-netconf/
├── run_cisco_gps_netconf.py   # Standalone launcher (adds src/ to path)
├── src/cisco_gps_netconf/
│   ├── cli.py                 # Argument parser and entry point
│   ├── gps_retriever.py       # NETCONF session and multi-source queries
│   ├── netconf_filters.py     # Subtree filters (tuple format required by ncclient)
│   ├── parsers.py             # XML parsing, DMS → decimal conversion
│   └── formatters.py          # Human-readable output
├── tests/                     # Unit tests with XML fixtures
└── pyproject.toml
```

## Supported platforms

| Platform | Status | Notes |
|----------|--------|-------|
| **IOS XE — IR1101, IR1800, IR1835, IR8340** | Tested | Cellular + GNSS/DR via `cellwan-oper` and `gnss-dr-oper` |
| **IOS XE — ISR with cellular** | Expected | Same YANG models as IR series |
| **IOS XE — CSR, Catalyst** | Partial | Depends on GPS hardware and YANG support |
| **IOS XR, Nexus** | Not implemented | Filter stubs exist; no retrieval logic yet |

IOS XE NETCONF subtree filters **must** use the `('subtree', '<xml>')` tuple form with ncclient. Raw XML strings alone produce `unknown-element` errors.

## Troubleshooting

| Symptom | Checks |
|---------|--------|
| Connection refused | `show netconf-yang statistics`, firewall on TCP 830 |
| Authentication failed | Privilege-15 user, correct credentials |
| No GPS sources returned | `show platform hardware gps detail`, `show cellular 0/x/y gps` |
| Cellular shows `gps-state-acquiring` | Wait for satellite lock; standalone mode can take longer than mbased |
| `gnss-oper` empty on IR1835 | Expected — use `GNSS_GPS_DR` / `gnss-dr-oper` instead |
| `unknown-element` NETCONF error | Ensure IOS XE 17.x+ with `netconf-yang`; filters must use subtree tuple |

### Useful router commands

```
show platform hardware gps detail
show cellular 0/4/0 gps
show cellular 0/5/0 gps
show cellular 0/5/0 radio
show netconf-yang statistics
```

## Development

```bash
pip install -e ".[dev]"
make test          # pytest with coverage
make format        # black
make lint          # flake8
```

CI runs on Python 3.9, 3.11, and 3.12 via GitHub Actions.

## Security

See [SECURITY.md](SECURITY.md). JSON output may contain precise location data — handle accordingly.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for parser/filter changes (XML fixtures preferred)
4. Run `pytest tests/`
5. Open a pull request

## License

MIT — see [LICENSE](LICENSE).

## Changelog

### v2.0.0

- NETCONF-only multi-source GPS retrieval (no SSH/CLI fallback)
- Correct IOS XE YANG models: `cellwan-oper`, `gnss-dr-oper`, `gnss-oper`
- DMS coordinate parsing from cellular NETCONF XML
- Platform GNSS source (`GNSS_GPS_DR`) mapped to `show platform hardware gps detail`
- Per-interface cellular radio metrics via `cellwan-radio`
- `--interfaces` filter; restructured package under `src/cisco_gps_netconf/`
- Verified on Cisco IR1835 (IOS XE 26.02)

### v1.1.0

- Cellular radio data (`--cellular`)
- DMS format parsing improvements

### v1.0.0

- Initial release
