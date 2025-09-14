# Cisco GPS NETCONF Retrieval Tool

A standalone Python script for retrieving GPS coordinates from Cisco routers using the NETCONF protocol. This tool supports multiple Cisco router platforms and YANG models, providing GPS coordinates in human-readable formats.

## Features

- **Multi-platform Support**: Works with IOS XE, IOS XR, and Nexus platforms
- **Multiple YANG Models**: Attempts various NETCONF filters to find GPS data
- **Multiple Output Formats**: 
  - Decimal degrees
  - Degrees, Minutes, Seconds (DMS)
  - Map service links (Google Maps, OpenStreetMap, Bing Maps)
- **Robust Error Handling**: Comprehensive error handling and troubleshooting information
- **JSON Export**: Save GPS data to JSON files for further processing
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
pip install ncclient xmltodict lxml

# Or use the requirements file
pip install -r requirements-standalone.txt
```

#### Option 2: System-wide Installation
```bash
pip install ncclient xmltodict lxml

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

## Usage

### Command Line Interface

```bash
# If using virtual environment, activate it first
source venv/bin/activate

# Basic usage
python cisco_gps_netconf.py -H 192.168.1.1 -u admin -p password

# With custom port and output file
python cisco_gps_netconf.py -H router.example.com -u netconf_user -p secret123 -P 2022 -o gps_data.json

# With timeout and verbose output
python cisco_gps_netconf.py -H 10.1.1.1 -u admin -p pass --timeout 60 -v

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

# Retrieve GPS coordinates
try:
    gps_data = gps_retriever.retrieve_and_display_gps(output_file="gps_data.json")
    print(f"Retrieved GPS data: {gps_data}")
except Exception as e:
    print(f"Error: {e}")
```

## Sample Output

```
============================================================
GPS COORDINATES RETRIEVED
============================================================
Decimal Degrees:
  Latitude:  37.7749°
  Longitude: -122.4194°

Degrees, Minutes, Seconds:
  Latitude:  37° 46' 29.64" N
  Longitude: 122° 25' 9.84" W

Map Links:
  Google Maps: https://www.google.com/maps?q=37.7749,-122.4194
  OpenStreetMap: https://www.openstreetmap.org/?mlat=37.7749&mlon=-122.4194&zoom=15
  Bing Maps: https://www.bing.com/maps?cp=37.7749~-122.4194&lvl=15

Altitude: 52.0 meters
Accuracy: 3.5 meters
============================================================
```

## Supported Platforms

- **Cisco IOS XE**: ASR 1000, ISR 4000, CSR 1000v, Catalyst 9000 series
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
   - Ensure GPS has satellite lock

### Debug Commands

Run these commands on your router to check GPS status:

```
show gps status
show location
show platform hardware gps status
show netconf-yang statistics
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/example/cisco-gps-netconf.git
cd cisco-gps-netconf
pip install ncclient xmltodict lxml
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

### v1.0.0 (2024-09-11)
- Initial release
- Support for IOS XE, IOS XR, and Nexus platforms
- Multiple output formats
- Command line interface
- JSON export functionality
- Comprehensive error handling
