# Cisco GPS NETCONF Retrieval Tool

A standalone Python script for retrieving GPS coordinates and cellular radio information from Cisco routers using the NETCONF protocol. This tool supports multiple Cisco router platforms and YANG models, providing GPS coordinates and cellular data in human-readable formats.

## Features

- **Multi-platform Support**: Works with IOS XE, IOS XR, and Nexus platforms
- **Cellular GPS & Radio Data**: Retrieve both GPS coordinates and cellular radio information
- **Multiple YANG Models**: Attempts various NETCONF filters to find GPS data
- **SSH Fallback**: Automatic fallback to SSH CLI commands when NETCONF is limited
- **Multiple Output Formats**: 
  - Decimal degrees
  - Degrees, Minutes, Seconds (DMS)
  - Map service links (Google Maps, OpenStreetMap, Bing Maps)
  - Cellular radio metrics (signal strength, band info, cell data)
- **Robust Error Handling**: Comprehensive error handling and troubleshooting information
- **JSON Export**: Save GPS and cellular data to JSON files for further processing
- **Command Line Interface**: Easy-to-use CLI tool

## Installation

### Download the Script
```bash
git clone https://github.com/example/cisco-gps-netconf.git
cd cisco-gps-netconf
```

### Install Dependencies

#### Option 1: Using Virtual Environment (Recommended)
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install ncclient xmltodict lxml paramiko

# Or use the requirements file
pip install -r requirements-standalone.txt
```

#### Option 2: System-wide Installation
```bash
pip install ncclient xmltodict lxml paramiko

# Or use the requirements file
pip install -r requirements-standalone.txt
```

**Note:** On some systems (like macOS with Homebrew Python), you may need to use a virtual environment or add `--user` flag to avoid "externally-managed-environment" errors.

### Make Script Executable (Optional)
```bash
chmod +x cisco_gps_netconf.py
```

## Prerequisites

### Router Configuration

Enable NETCONF on your Cisco router:

**For IOS XE:**
```
configure terminal
netconf ssh
username netconf_user privilege 15 secret your_password
ip ssh version 2
```

**For IOS XR:**
```
configure
netconf agent ssh
ssh server netconf vrf default
commit
```

### GPS Configuration

Ensure GPS is configured on your router:

**Basic GPS Configuration:**
```
configure terminal
gps enable
gps location latitude 37.7749 longitude -122.4194
```

**For Cellular GPS (ISR routers with cellular modules):**
```
configure terminal
interface cellular 0/5/0
 gps enable
 gps mode standalone
```

## Usage

### Command Line Interface

```bash
# If using virtual environment, activate it first
source venv/bin/activate

# Basic GPS usage
python cisco_gps_netconf.py -H 192.168.1.1 -u admin -p password

# GPS + Cellular radio data (recommended for cellular-enabled routers)
python cisco_gps_netconf.py -H 192.168.1.1 -u admin -p password --cellular

# With custom port and output file
python cisco_gps_netconf.py -H router.example.com -u netconf_user -p secret123 -P 2022 --cellular -o cellular_data.json

# With timeout and verbose output
python cisco_gps_netconf.py -H 10.1.1.1 -u admin -p pass --cellular --timeout 60 -v

# Show help and all options
python cisco_gps_netconf.py --help
```

### Using as a Python Module

You can also import and use the classes directly in your Python code:

```python
from cisco_gps_netconf import CiscoGPSRetriever

# Create retriever instance
gps_retriever = CiscoGPSRetriever(
    host="192.168.1.1",
    username="admin",
    password="password",
    port=830,
    timeout=30
)

# Retrieve GPS coordinates only
try:
    gps_data = gps_retriever.retrieve_and_display_gps(output_file="gps_data.json")
    print(f"Retrieved GPS data: {gps_data}")
except Exception as e:
    print(f"Error: {e}")

# Retrieve GPS + cellular radio data
try:
    cellular_data = gps_retriever.retrieve_and_display_cellular(output_file="cellular_data.json")
    print(f"Retrieved cellular data: {cellular_data}")
except Exception as e:
    print(f"Error: {e}")
```

## Sample Output

### GPS Only Mode
```
============================================================
GPS COORDINATES RETRIEVED
============================================================
Decimal Degrees:
  Latitude:  50.612334°
  Longitude: 5.586707°

Degrees, Minutes, Seconds:
  Latitude:  50° 36' 44.40" N
  Longitude: 5° 35' 12.15" E

Map Links:
  Google Maps: https://www.google.com/maps?q=50.612334,5.586707
  OpenStreetMap: https://www.openstreetmap.org/?mlat=50.612334&mlon=5.586707&zoom=15
  Bing Maps: https://www.bing.com/maps?cp=50.612334~5.586707&lvl=15

Altitude: 70 meters
HDOP: 0.6
Timestamp: Sun Sep 14 08:48:44 2025
Fix Type: 2D
GPS Status: GPS coordinates acquired
============================================================
```

### Cellular Mode (--cellular)
```
============================================================
CELLULAR DATA RETRIEVED
============================================================

GPS COORDINATES:
--------------------
Decimal Degrees:
  Latitude:  50.612334°
  Longitude: 5.586707°

Degrees, Minutes, Seconds:
  Latitude:  50° 36' 44.40" N
  Longitude: 5° 35' 12.15" E

Map Links:
  Google Maps: https://www.google.com/maps?q=50.612334,5.586707
  OpenStreetMap: https://www.openstreetmap.org/?mlat=50.612334&mlon=5.586707&zoom=15
  Bing Maps: https://www.bing.com/maps?cp=50.612334~5.586707&lvl=15

Altitude: 70 meters
HDOP: 0.6
Timestamp: Sun Sep 14 08:48:44 2025
Fix Type: 2D
GPS Status: GPS coordinates acquired


CELLULAR RADIO INFORMATION:
------------------------------
Power Mode: Online
LTE Band: B7
LTE Bandwidth: 10 MHz
LTE Rx Channel (PCC): 3175
LTE Tx Channel (PCC): 21175

Signal Strength:
  RSSI: -68 dBm
  RSRP: -93 dBm
  RSRQ: -13 dB
  SNR: 15.6 dB

Physical Cell ID: 114
Number of Nearby Cells: 1
RAT Preference: AUTO
RAT Selected: LTE
============================================================
```

## Supported Platforms

- **Cisco IOS XE**: ISR 1000, ISR 4000, CSR 1000v, Catalyst 9000 series
- **Cisco IOS XE with Cellular**: IR1101, IR1800, IR8340, ISR 1835 (cellular GPS and radio data)
- **Cisco IOS XR**: ASR 9000, NCS series
- **Cisco Nexus**: 9000 series (limited support)


## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Verify NETCONF is enabled on the router
   - Check network connectivity and firewall rules
   - Ensure correct IP address and port

2. **Authentication Failed**
   - Verify username and password
   - Check user privileges (should be privilege level 15)

3. **GPS Data Not Found**
   - Verify GPS is configured and enabled
   - Check GPS receiver status: `show gps status`
   - For cellular GPS: `show cellular 0/5/0 gps detail`
   - Ensure GPS has satellite lock

4. **NETCONF Limitations**
   - Some routers have limited NETCONF support
   - Script automatically falls back to SSH CLI commands
   - Use `--cellular` flag for comprehensive cellular data

### Debug Commands

Run these commands on your router to check GPS status:

```
# Standard GPS commands
show gps status
show location
show platform hardware gps status

# Cellular GPS commands
show cellular 0/5/0 gps detail
show cellular 0/5/0 radio
show cellular 0/5/0 network

# NETCONF status
show netconf-yang statistics
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/example/cisco-gps-netconf.git
cd cisco-gps-netconf
pip install ncclient xmltodict lxml paramiko
pip install pytest black mypy  # Optional development tools
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black cisco_gps_netconf.py
```

### Type Checking

```bash
mypy cisco_gps_netconf.py
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run tests and ensure they pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section in this README
- Review Cisco documentation for NETCONF and GPS configuration

## Changelog

### v1.1.0 (2024-09-14)
- Added cellular radio data support with `--cellular` flag
- Enhanced GPS parsing for DMS format coordinates
- Improved SSH fallback for routers with limited NETCONF support
- Added comprehensive cellular metrics (signal strength, band info, cell data)
- Better error handling and connection management

### v1.0.0 (2024-09-11)
- Initial release
- Support for IOS XE, IOS XR, and Nexus platforms
- Multiple output formats
- Command line interface
- JSON export functionality
- Comprehensive error handling
