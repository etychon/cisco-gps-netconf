"""
Main GPS retriever class for Cisco routers using NETCONF
"""

import sys
import xml.etree.ElementTree as ET
from ncclient import manager
from ncclient.operations.errors import RPCError
import json
from typing import Optional, Dict, Any, List
from .exceptions import CiscoGPSError, ConnectionError, AuthenticationError, GPSNotFoundError
from .formatters import CoordinateFormatter
from .netconf_filters import NetconfFilters


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
    
    def connect(self) -> manager.Manager:
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
    
    def get_gps_coordinates(self, connection: manager.Manager) -> Optional[Dict[str, Any]]:
        """
        Retrieve GPS coordinates using multiple methods
        
        Args:
            connection: Active NETCONF connection
            
        Returns:
            Dictionary containing GPS data or None if not found
        """
        # Try different filter methods
        methods = [
            ("IOS XE Native", self.filters.get_iosxe_native_filter()),
            ("IOS XE GPS", self.filters.get_iosxe_gps_filter()),
            ("Generic Location", self.filters.get_generic_location_filter()),
            ("Broad GPS", self.filters.get_broad_gps_filter())
        ]
        
        for method_name, gps_filter in methods:
            try:
                print(f"Trying {method_name} method...")
                response = connection.get(gps_filter)
                
                gps_data = self._extract_coordinates_from_response(response.xml)
                if gps_data:
                    print(f"✓ GPS data found using {method_name} method")
                    return gps_data
                    
            except RPCError as e:
                print(f"✗ {method_name} method failed: {e}")
                continue
            except Exception as e:
                print(f"✗ {method_name} method error: {e}")
                continue
        
        return None
    
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
            gps_data = self.get_gps_coordinates(connection)
            
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
            connection.close_session()
            print("\nNETCONF session closed.")
    
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
