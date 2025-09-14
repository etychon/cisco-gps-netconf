#!/usr/bin/env python3
"""
Cisco GPS NETCONF Retrieval Tool - Standalone Version

A standalone Python script for retrieving GPS coordinates from Cisco routers using NETCONF protocol.
This script supports multiple Cisco router platforms and YANG models, providing GPS coordinates 
in human-readable formats.

Requirements:
    pip install ncclient xmltodict lxml

Usage:
    python cisco_gps_netconf.py -H 192.168.1.1 -u admin -p password
    python cisco_gps_netconf.py -H router.example.com -u netconf_user -p secret123 -P 2022
    python cisco_gps_netconf.py -H 10.1.1.1 -u admin -p pass -o gps_data.json --timeout 60

Author: AI Assistant
Version: 1.0.0
License: MIT
"""

import sys
import xml.etree.ElementTree as ET
import json
import argparse
import re
from typing import Optional, Dict, Any, List

# Check for required dependencies
try:
    from ncclient import manager
    from ncclient.operations.errors import OperationError as RPCError
except ImportError:
    print("Error: Required dependency 'ncclient' not found.")
    print("Please install it with: pip install ncclient")
    sys.exit(1)

try:
    import xmltodict
except ImportError:
    print("Warning: 'xmltodict' not found. Install with: pip install xmltodict")
    xmltodict = None

try:
    import lxml
except ImportError:
    print("Warning: 'lxml' not found. Install with: pip install lxml")

try:
    import paramiko
except ImportError:
    print("Warning: 'paramiko' not found. SSH fallback will not be available.")
    print("Install with: pip install paramiko")
    paramiko = None


# ============================================================================
# EXCEPTIONS
# ============================================================================

class CiscoGPSError(Exception):
    """Base exception for Cisco GPS operations"""
    pass


class ConnectionError(CiscoGPSError):
    """Raised when connection to router fails"""
    pass


class AuthenticationError(CiscoGPSError):
    """Raised when authentication fails"""
    pass


class GPSNotFoundError(CiscoGPSError):
    """Raised when GPS data is not found on the router"""
    pass


class InvalidCoordinatesError(CiscoGPSError):
    """Raised when GPS coordinates are invalid or malformed"""
    pass


# ============================================================================
# NETCONF FILTERS
# ============================================================================

class NetconfFilters:
    """Collection of NETCONF filters for GPS data retrieval"""
    
    def get_iosxe_native_filter(self) -> str:
        """Get IOS XE native YANG model GPS filter"""
        return """
        <filter>
            <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
                <gps>
                    <location/>
                </gps>
            </native>
        </filter>
        """
    
    def get_iosxe_gps_filter(self) -> str:
        """Get IOS XE GPS-specific YANG model filter"""
        return """
        <filter>
            <gps xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-gps">
                <location/>
                <coordinates/>
            </gps>
        </filter>
        """
    
    def get_generic_location_filter(self) -> str:
        """Get generic location filter"""
        return """
        <filter>
            <location xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-location">
                <gps/>
                <coordinates/>
            </location>
        </filter>
        """
    
    def get_broad_gps_filter(self) -> str:
        """Get broad GPS filter without namespace restrictions"""
        return """
        <filter>
            <gps/>
        </filter>
        """
    
    def get_ios_xr_filter(self) -> str:
        """Get IOS XR GPS filter"""
        return """
        <filter>
            <gnss xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-gnss-oper">
                <gnss-receiver-info/>
            </gnss>
        </filter>
        """
    
    def get_nexus_filter(self) -> str:
        """Get Nexus GPS filter"""
        return """
        <filter>
            <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <gps-items/>
            </System>
        </filter>
        """
    
    def get_cellular_gps_filter(self) -> str:
        """Get cellular GPS filter for IOS XE"""
        return """
        <filter>
            <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
                <interface>
                    <Cellular>
                        <gps/>
                    </Cellular>
                </interface>
            </native>
        </filter>
        """
    
    def get_cellular_oper_filter(self) -> str:
        """Get cellular operational data filter"""
        return """
        <filter>
            <cellular-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-cellular-oper">
                <cellular-interface>
                    <gps/>
                </cellular-interface>
            </cellular-data>
        </filter>
        """
    
    def get_interfaces_oper_filter(self) -> str:
        """Get interfaces operational data with cellular GPS"""
        return """
        <filter>
            <interfaces xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-interfaces-oper">
                <interface>
                    <cellular-data>
                        <gps/>
                    </cellular-data>
                </interface>
            </interfaces>
        </filter>
        """
    
    def get_broad_cellular_filter(self) -> str:
        """Get broad cellular filter without specific namespace"""
        return """
        <filter>
            <cellular/>
        </filter>
        """
    
    def get_cellular_radio_filter(self) -> str:
        """Get cellular radio information filter"""
        return """
        <filter>
            <cellular-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-cellular-oper">
                <cellular-interface>
                    <radio/>
                </cellular-interface>
            </cellular-data>
        </filter>
        """
    
    def get_cellular_all_oper_filter(self) -> str:
        """Get all cellular operational data including radio and GPS"""
        return """
        <filter>
            <cellular-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-cellular-oper"/>
        </filter>
        """


# ============================================================================
# COORDINATE FORMATTER
# ============================================================================

class CoordinateFormatter:
    """Handles formatting of GPS coordinates in various formats"""
    
    def format_coordinates(self, gps_data: Dict[str, Any]) -> str:
        """
        Format GPS coordinates in human-readable format
        
        Args:
            gps_data: Dictionary containing GPS coordinates
            
        Returns:
            Formatted string with coordinates
        """
        if not gps_data:
            return "No GPS coordinates found"
        
        output = []
        output.append("=" * 60)
        output.append("GPS COORDINATES RETRIEVED")
        output.append("=" * 60)
        
        # Basic coordinates
        if 'latitude' in gps_data and 'longitude' in gps_data:
            lat = gps_data['latitude']
            lon = gps_data['longitude']
            
            output.append(f"Decimal Degrees:")
            output.append(f"  Latitude:  {lat}°")
            output.append(f"  Longitude: {lon}°")
            
            # Try to convert to DMS format if possible
            try:
                lat_float = float(lat)
                lon_float = float(lon)
                
                lat_dms = self._decimal_to_dms(lat_float, 'latitude')
                lon_dms = self._decimal_to_dms(lon_float, 'longitude')
                
                output.append(f"\nDegrees, Minutes, Seconds:")
                output.append(f"  Latitude:  {lat_dms}")
                output.append(f"  Longitude: {lon_dms}")
                
                # Add coordinate links
                output.extend(self._generate_map_links(lat_float, lon_float))
                
            except ValueError:
                output.append(f"\nNote: Could not convert to DMS format (non-numeric values)")
        
        # Additional GPS information
        self._add_additional_info(output, gps_data)
        
        output.append("=" * 60)
        return "\n".join(output)
    
    def _decimal_to_dms(self, decimal_degrees: float, coord_type: str) -> str:
        """
        Convert decimal degrees to degrees, minutes, seconds format
        
        Args:
            decimal_degrees: Coordinate in decimal degrees
            coord_type: 'latitude' or 'longitude'
            
        Returns:
            Formatted DMS string
        """
        is_negative = decimal_degrees < 0
        decimal_degrees = abs(decimal_degrees)
        
        degrees = int(decimal_degrees)
        minutes_float = (decimal_degrees - degrees) * 60
        minutes = int(minutes_float)
        seconds = (minutes_float - minutes) * 60
        
        # Determine direction
        if coord_type == 'latitude':
            direction = 'S' if is_negative else 'N'
        else:  # longitude
            direction = 'W' if is_negative else 'E'
        
        return f"{degrees}° {minutes}' {seconds:.2f}\" {direction}"
    
    def _generate_map_links(self, lat: float, lon: float) -> List[str]:
        """Generate links to various map services"""
        links = [
            f"\nMap Links:",
            f"  Google Maps: https://www.google.com/maps?q={lat},{lon}",
            f"  OpenStreetMap: https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=15",
            f"  Bing Maps: https://www.bing.com/maps?cp={lat}~{lon}&lvl=15"
        ]
        return links
    
    def _add_additional_info(self, output: List[str], gps_data: Dict[str, Any]):
        """Add additional GPS information to the output"""
        
        # Altitude
        if 'altitude' in gps_data:
            output.append(f"\nAltitude: {gps_data['altitude']}")
        
        # Accuracy
        if 'accuracy' in gps_data:
            output.append(f"Accuracy: {gps_data['accuracy']}")
        
        # Timestamp
        if 'timestamp' in gps_data:
            output.append(f"Timestamp: {gps_data['timestamp']}")
        
        # Additional GPS data
        excluded_keys = {'latitude', 'longitude', 'altitude', 'accuracy', 'timestamp'}
        other_data = {k: v for k, v in gps_data.items() if k not in excluded_keys}
        
        if other_data:
            output.append(f"\nAdditional GPS Data:")
            for key, value in other_data.items():
                output.append(f"  {key.replace('_', ' ').title()}: {value}")


# ============================================================================
# MAIN GPS RETRIEVER CLASS
# ============================================================================

class CiscoGPSRetriever:
    """Class to handle GPS coordinate retrieval from Cisco routers via NETCONF"""
    
    def __init__(self, host: str, port: int = 830, username: str = "", password: str = "", timeout: int = 30):
        """
        Initialize the GPS retriever
        
        Args:
            host: Router IP address or hostname
            port: NETCONF port (default: 830)
            username: Router username
            password: Router password
            timeout: Connection timeout in seconds
        """
        self.connection_params = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "hostkey_verify": False,
            "timeout": timeout,
            "device_params": {"name": "iosxe"}
        }
        self.formatter = CoordinateFormatter()
        self.filters = NetconfFilters()
    
    def connect(self):
        """Establish NETCONF connection to the router"""
        try:
            print(f"Connecting to {self.connection_params['host']}:{self.connection_params['port']}...")
            connection = manager.connect(**self.connection_params)
            print("✓ NETCONF connection established successfully")
            return connection
        except Exception as e:
            if "authentication failed" in str(e).lower():
                raise AuthenticationError(f"Authentication failed: {e}")
            else:
                raise ConnectionError(f"Failed to connect: {e}")
    
    def get_gps_coordinates(self, connection) -> tuple[Optional[Dict[str, Any]], Any]:
        """
        Retrieve GPS coordinates using multiple methods
        
        Args:
            connection: Active NETCONF connection
            
        Returns:
            Tuple of (GPS data dictionary or None, updated connection)
        """
        # Try different filter methods - prioritize cellular GPS methods first
        methods = [
            ("Cellular GPS Native", self.filters.get_cellular_gps_filter()),
            ("Cellular Operational", self.filters.get_cellular_oper_filter()),
            ("Interfaces Operational", self.filters.get_interfaces_oper_filter()),
            ("Broad Cellular", self.filters.get_broad_cellular_filter()),
            ("IOS XE Native", self.filters.get_iosxe_native_filter()),
            ("IOS XE GPS", self.filters.get_iosxe_gps_filter()),
            ("Generic Location", self.filters.get_generic_location_filter()),
            ("Broad GPS", self.filters.get_broad_gps_filter())
        ]
        
        for method_name, gps_filter in methods:
            try:
                print(f"Trying {method_name} method...")
                
                # Try to get response, but handle parsing errors
                try:
                    response = connection.get(gps_filter)
                    xml_data = response.xml
                except Exception as parse_error:
                    print(f"Parse error: {parse_error}")
                    # Try to get raw response if available
                    if hasattr(connection, '_session') and hasattr(connection._session, '_buffer'):
                        print("Attempting to get raw response...")
                        # This is a fallback - may not always work
                    continue
                
                # Debug: Print the XML response
                print(f"Response XML length: {len(xml_data)} characters")
                if len(xml_data) < 2000:  # Only print if not too long
                    print(f"Response XML: {xml_data}")
                else:
                    print(f"Response XML (truncated): {xml_data[:1000]}...")
                
                gps_data = self._extract_coordinates_from_response(xml_data)
                if gps_data:
                    print(f"✓ GPS data found using {method_name} method")
                    return gps_data, connection
                else:
                    print(f"✗ No GPS coordinates found in {method_name} response")
                    
            except RPCError as e:
                print(f"✗ {method_name} method failed: {e}")
                continue
            except Exception as e:
                print(f"✗ {method_name} method error: {e}")
                # For connection errors, try to reconnect
                if "not connected" in str(e).lower():
                    try:
                        print("Attempting to reconnect...")
                        connection = self.connect()
                    except:
                        print("Reconnection failed, continuing with next method")
                continue
        
        return None, connection
    
    def _extract_coordinates_from_response(self, xml_response: str) -> Optional[Dict[str, Any]]:
        """
        Extract GPS coordinates from XML response
        
        Args:
            xml_response: XML response string
            
        Returns:
            Dictionary with GPS coordinates or None
        """
        try:
            root = ET.fromstring(xml_response)
            return self._extract_coordinates_from_xml(root)
        except ET.ParseError as e:
            print(f"XML parsing error: {e}")
            return None
    
    def _extract_coordinates_from_xml(self, root: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Extract GPS coordinates from XML element tree
        
        Args:
            root: XML root element
            
        Returns:
            Dictionary with GPS coordinates or None
        """
        gps_data = {}
        
        # Search for latitude, longitude, and altitude in the XML tree
        for elem in root.iter():
            text = elem.text
            tag_lower = elem.tag.lower() if elem.tag else ""
            
            if text and text.strip():
                if any(keyword in tag_lower for keyword in ['latitude', 'lat']):
                    gps_data['latitude'] = text.strip()
                elif any(keyword in tag_lower for keyword in ['longitude', 'lon', 'lng']):
                    gps_data['longitude'] = text.strip()
                elif any(keyword in tag_lower for keyword in ['altitude', 'alt', 'elevation']):
                    gps_data['altitude'] = text.strip()
                elif 'accuracy' in tag_lower:
                    gps_data['accuracy'] = text.strip()
                elif 'timestamp' in tag_lower:
                    gps_data['timestamp'] = text.strip()
        
        return gps_data if len(gps_data) >= 2 else None
    
    def _extract_gps_from_cli_output(self, output: str) -> Optional[Dict[str, Any]]:
        """Extract GPS coordinates from CLI output"""
        gps_data = {}
        
        # Look for DMS format: "50 Deg 36 Min 44.3874 Sec North"
        lat_dms_pattern = r'Latitude\s*=\s*(\d+)\s+Deg\s+(\d+)\s+Min\s+([\d.]+)\s+Sec\s+(North|South)'
        lon_dms_pattern = r'Longitude\s*=\s*(\d+)\s+Deg\s+(\d+)\s+Min\s+([\d.]+)\s+Sec\s+(East|West)'
        
        lat_match = re.search(lat_dms_pattern, output, re.IGNORECASE)
        lon_match = re.search(lon_dms_pattern, output, re.IGNORECASE)
        
        if lat_match:
            degrees = int(lat_match.group(1))
            minutes = int(lat_match.group(2))
            seconds = float(lat_match.group(3))
            direction = lat_match.group(4).upper()
            
            # Convert to decimal degrees
            decimal_lat = degrees + minutes/60 + seconds/3600
            if direction == 'SOUTH':
                decimal_lat = -decimal_lat
                
            gps_data['latitude'] = str(decimal_lat)
            gps_data['latitude_dms'] = f"{degrees}° {minutes}' {seconds}\" {direction[0]}"
        
        if lon_match:
            degrees = int(lon_match.group(1))
            minutes = int(lon_match.group(2))
            seconds = float(lon_match.group(3))
            direction = lon_match.group(4).upper()
            
            # Convert to decimal degrees
            decimal_lon = degrees + minutes/60 + seconds/3600
            if direction == 'WEST':
                decimal_lon = -decimal_lon
                
            gps_data['longitude'] = str(decimal_lon)
            gps_data['longitude_dms'] = f"{degrees}° {minutes}' {seconds}\" {direction[0]}"
        
        # Look for height/altitude
        height_pattern = r'Height\s*=\s*([\d.]+)m'
        height_match = re.search(height_pattern, output, re.IGNORECASE)
        if height_match:
            gps_data['altitude'] = height_match.group(1) + " meters"
        
        # Look for other GPS info patterns
        patterns = {
            'hdop': r'HDOP\s*=\s*([\d.]+)',
            'timestamp': r'Timestamp\s*\(GMT\)\s*=\s*([^\n\r]+)',
            'fix_type': r'Fix type\s*=\s*([^,\n\r]+)',
            'gps_status': r'GPS Status\s*=\s*([^\n\r]+)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                gps_data[key] = match.group(1).strip()
        
        return gps_data if len(gps_data) >= 2 else None
    
    def _extract_radio_from_cli_output(self, output: str) -> Optional[Dict[str, Any]]:
        """Extract cellular radio information from CLI output"""
        radio_data = {}
        
        # Define patterns for radio information
        patterns = {
            'power_mode': r'Radio power mode\s*=\s*([^\n\r]+)',
            'lte_rx_channel': r'LTE Rx Channel Number\(PCC\)\s*=\s*(\d+)',
            'lte_tx_channel': r'LTE Tx Channel Number\(PCC\)\s*=\s*(\d+)',
            'lte_band': r'LTE Band\s*=\s*([^\n\r]+)',
            'lte_bandwidth': r'LTE Bandwidth\s*=\s*([^\n\r]+)',
            'rssi': r'Current RSSI\s*=\s*([+-]?\d+\.?\d*)\s*dBm',
            'rsrp': r'Current RSRP\s*=\s*([+-]?\d+\.?\d*)\s*dBm',
            'rsrq': r'Current RSRQ\s*=\s*([+-]?\d+\.?\d*)\s*dB',
            'snr': r'Current SNR\s*=\s*([+-]?\d+\.?\d*)\s*dB',
            'physical_cell_id': r'Physical Cell ID\s*=\s*(\d+)',
            'nearby_cells': r'Number of nearby cells\s*=\s*(\d+)',
            'rat_preference': r'Radio Access Technology\(RAT\) Preference\s*=\s*([^\n\r]+)',
            'rat_selected': r'Radio Access Technology\(RAT\) Selected\s*=\s*([^\n\r]+)',
            'network_change_event': r'Network Change Event\s*=\s*([^\n\r]+)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                radio_data[key] = match.group(1).strip()
        
        # Extract nearby cell IDs if present
        cell_ids = []
        cell_pattern = r'(\d+)\s+(\d+)'  # Index and PCI
        cell_matches = re.findall(cell_pattern, output)
        if cell_matches:
            for idx, pci in cell_matches:
                if idx.isdigit() and pci.isdigit():
                    cell_ids.append({'index': idx, 'pci': pci})
            if cell_ids:
                radio_data['nearby_cell_ids'] = cell_ids
        
        return radio_data if radio_data else None
    
    def _try_ssh_gps_fallback(self) -> Optional[Dict[str, Any]]:
        """Try to get GPS data via SSH CLI commands as fallback"""
        if not paramiko:
            print("SSH fallback not available (paramiko not installed)")
            return None
            
        print("\n" + "="*50)
        print("NETCONF failed, trying SSH fallback...")
        print("="*50)
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            print("Connecting via SSH...")
            ssh.connect(
                self.connection_params['host'], 
                username=self.connection_params['username'], 
                password=self.connection_params['password'],
                port=22, 
                timeout=self.connection_params['timeout'], 
                allow_agent=False, 
                look_for_keys=False
            )
            
            print("✓ SSH connection established")
            
            # Try cellular GPS commands
            commands = [
                'show cellular 0/5/0 gps detail',
                'show cellular 0/5/0 gps',
                'show gps status',
                'show location'
            ]
            
            for cmd in commands:
                try:
                    print(f"Executing: {cmd}")
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    
                    # Wait for command to complete
                    exit_status = stdout.channel.recv_exit_status()
                    output = stdout.read().decode('utf-8')
                    
                    if exit_status == 0 and output:
                        gps_data = self._extract_gps_from_cli_output(output)
                        if gps_data:
                            print(f"✓ GPS data found via SSH command: {cmd}")
                            return gps_data
                        else:
                            print(f"✗ No GPS coordinates found in '{cmd}' output")
                    else:
                        print(f"✗ Command '{cmd}' failed with exit status {exit_status}")
                        
                except Exception as e:
                    print(f"Command '{cmd}' failed: {e}")
                    continue
            
            return None
            
        except Exception as e:
            print(f"SSH connection failed: {e}")
            return None
        finally:
            ssh.close()
    
    def _execute_ssh_command(self, command: str) -> tuple[int, str, str]:
        """Execute a single SSH command with a fresh connection"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(
                self.connection_params['host'], 
                username=self.connection_params['username'], 
                password=self.connection_params['password'],
                port=22, 
                timeout=self.connection_params['timeout'], 
                allow_agent=False, 
                look_for_keys=False
            )
            
            stdin, stdout, stderr = ssh.exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8')
            error_output = stderr.read().decode('utf-8')
            
            return exit_status, output, error_output
            
        except Exception as e:
            return -1, "", str(e)
        finally:
            ssh.close()
    
    def _try_ssh_cellular_fallback(self) -> Dict[str, Any]:
        """Try to get both GPS and radio data via SSH CLI commands as fallback"""
        if not paramiko:
            print("SSH fallback not available (paramiko not installed)")
            return {}
            
        print("\n" + "="*50)
        print("NETCONF failed, trying SSH fallback for cellular data...")
        print("="*50)
        
        cellular_data = {}
        
        # Commands for both GPS and radio data
        commands = [
            'show cellular 0/5/0 gps detail',
            'show cellular 0/5/0 gps',
            'show cellular 0/5/0 radio',
            'show cellular 0/5/0 network',
            'show gps status',
            'show location'
        ]
        
        for cmd in commands:
            try:
                print(f"Executing: {cmd}")
                exit_status, output, error_output = self._execute_ssh_command(cmd)
                
                if exit_status == 0 and output:
                    # Try GPS parsing first
                    gps_data = self._extract_gps_from_cli_output(output)
                    if gps_data:
                        print(f"✓ GPS data found via SSH command: {cmd}")
                        cellular_data.update(gps_data)
                    
                    # Try radio parsing
                    radio_data = self._extract_radio_from_cli_output(output)
                    if radio_data:
                        print(f"✓ Radio data found via SSH command: {cmd}")
                        # Prefix radio data keys to avoid conflicts
                        for key, value in radio_data.items():
                            cellular_data[f'radio_{key}'] = value
                    
                    # If neither GPS nor radio data found, show output for debugging
                    if not gps_data and not radio_data:
                        print(f"✗ No GPS or radio data found in '{cmd}' output")
                        if len(output) < 500:
                            print(f"Output: {output}")
                else:
                    print(f"✗ Command '{cmd}' failed with exit status {exit_status}")
                    if error_output:
                        print(f"Error: {error_output}")
                    
            except Exception as e:
                print(f"Command '{cmd}' failed: {e}")
                continue
        
        return cellular_data
    
    def retrieve_and_display_cellular(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Main method to retrieve and display both GPS and cellular radio data
        
        Args:
            output_file: Optional file path to save cellular data
            
        Returns:
            Dictionary containing GPS and radio data
        """
        connection = self.connect()
        
        try:
            # Try NETCONF first with cellular-specific filters
            cellular_data = {}
            
            # Add radio filters to the methods list
            radio_methods = [
                ("Cellular All Operational", self.filters.get_cellular_all_oper_filter()),
                ("Cellular Radio", self.filters.get_cellular_radio_filter()),
            ]
            
            # Try radio-specific NETCONF methods first
            for method_name, cellular_filter in radio_methods:
                try:
                    print(f"Trying {method_name} method...")
                    
                    try:
                        response = connection.get(cellular_filter)
                        xml_data = response.xml
                    except Exception as parse_error:
                        print(f"Parse error: {parse_error}")
                        continue
                    
                    print(f"Response XML length: {len(xml_data)} characters")
                    if len(xml_data) < 2000:
                        print(f"Response XML: {xml_data}")
                    else:
                        print(f"Response XML (truncated): {xml_data[:1000]}...")
                    
                    # Try to extract any data from the response
                    extracted_data = self._extract_coordinates_from_response(xml_data)
                    if extracted_data:
                        print(f"✓ Data found using {method_name} method")
                        cellular_data.update(extracted_data)
                        
                except Exception as e:
                    print(f"✗ {method_name} method error: {e}")
                    continue
            
            # Try the original GPS methods
            gps_data, connection = self.get_gps_coordinates(connection)
            if gps_data:
                cellular_data.update(gps_data)
            
            if cellular_data:
                # Display formatted data
                formatted_output = self._format_cellular_data(cellular_data)
                print(formatted_output)
                
                # Save to file if requested
                if output_file:
                    self._save_gps_data(cellular_data, output_file)
                
                return cellular_data
            else:
                # Try SSH fallback for both GPS and radio
                print("NETCONF methods failed, trying SSH fallback...")
                cellular_data = self._try_ssh_cellular_fallback()
                
                if cellular_data:
                    # Display formatted data
                    formatted_output = self._format_cellular_data(cellular_data)
                    print(formatted_output)
                    
                    # Save to file if requested
                    if output_file:
                        self._save_gps_data(cellular_data, output_file)
                    
                    return cellular_data
                else:
                    error_msg = self._generate_troubleshooting_info()
                    print(error_msg)
                    raise GPSNotFoundError("No cellular data found on the router")
                
        finally:
            if connection:
                try:
                    connection.close_session()
                    print("\nNETCONF session closed.")
                except:
                    print("\nNETCONF session already closed.")
    
    def _format_cellular_data(self, cellular_data: Dict[str, Any]) -> str:
        """Format both GPS and radio data for display"""
        output = []
        output.append("=" * 60)
        output.append("CELLULAR DATA RETRIEVED")
        output.append("=" * 60)
        
        # GPS Section
        gps_keys = ['latitude', 'longitude', 'altitude', 'hdop', 'timestamp', 'fix_type', 'gps_status']
        gps_data = {k: v for k, v in cellular_data.items() if k in gps_keys or 'dms' in k}
        
        if gps_data:
            output.append("\nGPS COORDINATES:")
            output.append("-" * 20)
            
            if 'latitude' in gps_data and 'longitude' in gps_data:
                lat = gps_data['latitude']
                lon = gps_data['longitude']
                
                output.append(f"Decimal Degrees:")
                output.append(f"  Latitude:  {lat}°")
                output.append(f"  Longitude: {lon}°")
                
                # Add DMS format if available
                if 'latitude_dms' in gps_data and 'longitude_dms' in gps_data:
                    output.append(f"\nDegrees, Minutes, Seconds:")
                    output.append(f"  Latitude:  {gps_data['latitude_dms']}")
                    output.append(f"  Longitude: {gps_data['longitude_dms']}")
                
                # Add map links
                try:
                    lat_float = float(lat)
                    lon_float = float(lon)
                    output.append(f"\nMap Links:")
                    output.append(f"  Google Maps: https://www.google.com/maps?q={lat_float},{lon_float}")
                    output.append(f"  OpenStreetMap: https://www.openstreetmap.org/?mlat={lat_float}&mlon={lon_float}&zoom=15")
                    output.append(f"  Bing Maps: https://www.bing.com/maps?cp={lat_float}~{lon_float}&lvl=15")
                except ValueError:
                    pass
            
            # Add other GPS info
            if 'altitude' in gps_data:
                output.append(f"\nAltitude: {gps_data['altitude']}")
            if 'hdop' in gps_data:
                output.append(f"HDOP: {gps_data['hdop']}")
            if 'timestamp' in gps_data:
                output.append(f"Timestamp: {gps_data['timestamp']}")
            if 'fix_type' in gps_data:
                output.append(f"Fix Type: {gps_data['fix_type']}")
            if 'gps_status' in gps_data:
                output.append(f"GPS Status: {gps_data['gps_status']}")
        
        # Radio Section
        radio_data = {k: v for k, v in cellular_data.items() if k.startswith('radio_')}
        
        if radio_data:
            output.append(f"\n\nCELLULAR RADIO INFORMATION:")
            output.append("-" * 30)
            
            # Power and basic info
            if 'radio_power_mode' in radio_data:
                output.append(f"Power Mode: {radio_data['radio_power_mode']}")
            
            # LTE Band and Channel info
            if 'radio_lte_band' in radio_data:
                output.append(f"LTE Band: {radio_data['radio_lte_band']}")
            if 'radio_lte_bandwidth' in radio_data:
                output.append(f"LTE Bandwidth: {radio_data['radio_lte_bandwidth']}")
            if 'radio_lte_rx_channel' in radio_data:
                output.append(f"LTE Rx Channel (PCC): {radio_data['radio_lte_rx_channel']}")
            if 'radio_lte_tx_channel' in radio_data:
                output.append(f"LTE Tx Channel (PCC): {radio_data['radio_lte_tx_channel']}")
            
            # Signal strength
            output.append(f"\nSignal Strength:")
            if 'radio_rssi' in radio_data:
                output.append(f"  RSSI: {radio_data['radio_rssi']} dBm")
            if 'radio_rsrp' in radio_data:
                output.append(f"  RSRP: {radio_data['radio_rsrp']} dBm")
            if 'radio_rsrq' in radio_data:
                output.append(f"  RSRQ: {radio_data['radio_rsrq']} dB")
            if 'radio_snr' in radio_data:
                output.append(f"  SNR: {radio_data['radio_snr']} dB")
            
            # Cell info
            if 'radio_physical_cell_id' in radio_data:
                output.append(f"\nPhysical Cell ID: {radio_data['radio_physical_cell_id']}")
            if 'radio_nearby_cells' in radio_data:
                output.append(f"Number of Nearby Cells: {radio_data['radio_nearby_cells']}")
            
            # RAT info
            if 'radio_rat_preference' in radio_data:
                output.append(f"RAT Preference: {radio_data['radio_rat_preference']}")
            if 'radio_rat_selected' in radio_data:
                output.append(f"RAT Selected: {radio_data['radio_rat_selected']}")
            
            # Nearby cells
            if 'radio_nearby_cell_ids' in radio_data:
                output.append(f"\nNearby Cell IDs:")
                for cell in radio_data['radio_nearby_cell_ids']:
                    output.append(f"  Index {cell['index']}: PCI {cell['pci']}")
        
        output.append("=" * 60)
        return "\n".join(output)
    
    def retrieve_and_display_gps(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Main method to retrieve and display GPS coordinates
        
        Args:
            output_file: Optional file path to save GPS data
            
        Returns:
            Dictionary containing GPS data
        """
        connection = self.connect()
        
        try:
            gps_data, connection = self.get_gps_coordinates(connection)
            
            if gps_data:
                # Display formatted coordinates
                formatted_output = self.formatter.format_coordinates(gps_data)
                print(formatted_output)
                
                # Save to file if requested
                if output_file:
                    self._save_gps_data(gps_data, output_file)
                
                return gps_data
            else:
                # Try SSH fallback if NETCONF failed
                print("NETCONF methods failed, trying SSH fallback...")
                gps_data = self._try_ssh_gps_fallback()
                
                if gps_data:
                    # Display formatted coordinates
                    formatted_output = self.formatter.format_coordinates(gps_data)
                    print(formatted_output)
                    
                    # Save to file if requested
                    if output_file:
                        self._save_gps_data(gps_data, output_file)
                    
                    return gps_data
                else:
                    error_msg = self._generate_troubleshooting_info()
                    print(error_msg)
                    raise GPSNotFoundError("No GPS coordinates found on the router")
                
        finally:
            if connection:
                try:
                    connection.close_session()
                    print("\nNETCONF session closed.")
                except:
                    print("\nNETCONF session already closed.")
    
    def _save_gps_data(self, gps_data: Dict[str, Any], filename: str):
        """Save GPS data to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(gps_data, f, indent=2)
            print(f"\nGPS data saved to: {filename}")
        except Exception as e:
            print(f"Warning: Could not save GPS data to file: {e}")
    
    def _generate_troubleshooting_info(self) -> str:
        """Generate troubleshooting information when GPS is not found"""
        return """
========================================
NO GPS COORDINATES FOUND
========================================
Possible reasons:
- GPS is not configured on the router
- GPS receiver is not connected or malfunctioning
- Router does not support GPS functionality
- Different YANG model is used than expected
- Insufficient user permissions
- GPS satellite lock not established

Troubleshooting steps:
1. Check router GPS status:
   - show gps status
   - show location
   - show platform hardware gps status

2. Verify GPS configuration:
   - gps enable
   - gps location latitude <value> longitude <value>

3. Check NETCONF capabilities:
   - show netconf-yang statistics

4. Verify user permissions for NETCONF access
========================================
"""


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="Retrieve GPS coordinates and cellular radio data from Cisco router via NETCONF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # GPS only
    python cisco_gps_netconf.py -H 192.168.1.1 -u admin -p password
    
    # GPS and cellular radio data
    python cisco_gps_netconf.py -H 192.168.1.1 -u admin -p password --cellular
    
    # With custom port and output file
    python cisco_gps_netconf.py -H router.example.com -u netconf_user -p secret123 -P 2022 --cellular -o cellular_data.json

Dependencies:
    pip install ncclient xmltodict lxml

Supported Platforms:
    - Cisco IOS XE: ASR 1000, ISR 4000, CSR 1000v, Catalyst 9000 series
    - Cisco IOS XR: ASR 9000, NCS series  
    - Cisco Nexus: 9000 series (limited support)
        """
    )
    
    # Required arguments
    parser.add_argument('-H', '--host', required=True, 
                       help='Router IP address or hostname')
    parser.add_argument('-u', '--username', required=True,
                       help='Router username')
    parser.add_argument('-p', '--password', required=True,
                       help='Router password')
    
    # Optional arguments
    parser.add_argument('-P', '--port', type=int, default=830,
                       help='NETCONF port (default: 830)')
    parser.add_argument('-o', '--output', 
                       help='Output file to save GPS data (JSON format)')
    parser.add_argument('-t', '--timeout', type=int, default=30,
                       help='Connection timeout in seconds (default: 30)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--cellular', action='store_true',
                       help='Retrieve both GPS and cellular radio data')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    
    return parser


def main():
    """Main CLI function"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Create GPS retriever instance
    try:
        gps_retriever = CiscoGPSRetriever(
            host=args.host,
            port=args.port,
            username=args.username,
            password=args.password,
            timeout=args.timeout
        )
        
        # Retrieve and display data based on options
        if args.cellular:
            # Retrieve both GPS and cellular radio data
            cellular_data = gps_retriever.retrieve_and_display_cellular(output_file=args.output)
            
            if args.verbose:
                print(f"\nRaw cellular data: {cellular_data}")
        else:
            # Retrieve GPS data only
            gps_data = gps_retriever.retrieve_and_display_gps(output_file=args.output)
            
            if args.verbose:
                print(f"\nRaw GPS data: {gps_data}")
        
        sys.exit(0)
        
    except CiscoGPSError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    main()
