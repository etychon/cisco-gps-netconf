"""
Main GPS retriever class for Cisco routers using NETCONF
"""

import json
from typing import Optional, Dict, Any, List

from ncclient import manager

from .exceptions import ConnectionError, AuthenticationError, GPSNotFoundError
from .formatters import CoordinateFormatter
from .netconf_filters import NetconfFilters
from .parsers import parse_gps_sources_from_xml, parse_radio_from_xml


class CiscoGPSRetriever:
    """Retrieve GPS coordinates from Cisco IOS XE routers via NETCONF."""

    def __init__(
        self,
        host: str,
        port: int = 830,
        username: str = "",
        password: str = "",
        timeout: int = 30,
        interfaces: Optional[List[str]] = None,
    ):
        self.connection_params = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "hostkey_verify": False,
            "timeout": timeout,
            "device_params": {"name": "iosxe"},
        }
        self.interfaces = interfaces
        self.formatter = CoordinateFormatter()
        self.filters = NetconfFilters()

    def connect(self) -> manager.Manager:
        """Establish NETCONF connection to the router."""
        try:
            print(
                f"Connecting to {self.connection_params['host']}:"
                f"{self.connection_params['port']}..."
            )
            connection = manager.connect(**self.connection_params)
            print("NETCONF connection established successfully")
            return connection
        except Exception as e:
            if "authentication failed" in str(e).lower():
                raise AuthenticationError(f"Authentication failed: {e}")
            raise ConnectionError(f"Failed to connect: {e}")

    def _netconf_get(self, connection: manager.Manager, netconf_filter) -> Optional[str]:
        """Run a NETCONF get and return XML, or None on failure."""
        try:
            response = connection.get(netconf_filter)
            return response.xml
        except Exception as e:
            print(f"NETCONF get failed: {e}")
            return None

    def _log_gnss_oper_status(self, xml: str) -> None:
        """Explain when Cisco-IOS-XE-gnss-oper has no usable fix on this platform."""
        if "fix-no-fix" in xml and "latitude" not in xml.lower():
            print(
                "  Cisco-IOS-XE-gnss-oper: no location fix "
                "(on IR1835 the platform GNSS module is exposed via gnss-dr-oper)"
            )

    def get_all_gps_sources(self, connection: manager.Manager) -> Dict[str, Dict[str, Any]]:
        """
        Collect GPS coordinates from all available NETCONF operational sources.

        Skips sources that are unavailable or have no fix.
        """
        sources: Dict[str, Dict[str, Any]] = {}

        queries = [
            ("GNSS/GPS/DR module (platform hardware GPS)", self.filters.get_gnss_dr_oper_filter()),
            ("Cellular GPS", self.filters.get_cellwan_gps_filter()),
            ("GNSS slot module (gnss-oper)", self.filters.get_gnss_oper_filter()),
        ]

        for label, netconf_filter in queries:
            print(f"Querying {label}...")
            xml = self._netconf_get(connection, netconf_filter)
            if not xml:
                continue

            if "gnss-oper-data" in xml:
                self._log_gnss_oper_status(xml)

            found = parse_gps_sources_from_xml(xml)
            for source_id, data in found.items():
                if self.interfaces and data.get("source_type") == "cellular":
                    if source_id not in self.interfaces:
                        continue
                if source_id not in sources:
                    sources[source_id] = data
                    print(f"  Found coordinates for {source_id}")

        return sources

    def get_all_radio_data(self, connection: manager.Manager) -> Dict[str, Dict[str, Any]]:
        """Collect cellular radio metrics from cellwan-radio operational data."""
        print("Querying cellular radio data...")
        xml = self._netconf_get(connection, self.filters.get_cellwan_radio_filter())
        if not xml:
            return {}

        radios = parse_radio_from_xml(xml)
        if self.interfaces:
            radios = {k: v for k, v in radios.items() if k in self.interfaces}

        for iface in radios:
            print(f"  Found radio data for {iface}")
        return radios

    def retrieve_and_display_gps(
        self, output_file: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Retrieve and display all available GPS sources."""
        connection = self.connect()
        try:
            sources = self.get_all_gps_sources(connection)
            if not sources:
                print(self._generate_troubleshooting_info())
                raise GPSNotFoundError("No GPS coordinates found on the router")

            print(self.formatter.format_all_sources(sources))
            if output_file:
                self._save_data(sources, output_file)
            return sources
        finally:
            connection.close_session()
            print("\nNETCONF session closed.")

    def retrieve_and_display_cellular(
        self, output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retrieve GPS sources and per-interface cellular radio data."""
        connection = self.connect()
        try:
            sources = self.get_all_gps_sources(connection)
            radios = self.get_all_radio_data(connection)

            if not sources and not radios:
                print(self._generate_troubleshooting_info())
                raise GPSNotFoundError("No cellular data found on the router")

            report = {"gps_sources": sources, "radio": radios}
            print(self.formatter.format_cellular_report(sources, radios))
            if output_file:
                self._save_data(report, output_file)
            return report
        finally:
            connection.close_session()
            print("\nNETCONF session closed.")

    def _save_data(self, data: Dict[str, Any], filename: str) -> None:
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"\nData saved to: {filename}")
        except OSError as e:
            print(f"Warning: Could not save data to file: {e}")

    def _generate_troubleshooting_info(self) -> str:
        return """
========================================
NO GPS COORDINATES FOUND
========================================
Possible reasons:
- GPS is not configured on the router
- GPS receiver has no satellite fix
- Operational YANG models not available on this IOS XE release
- Insufficient NETCONF user permissions

NETCONF models used by this tool:
- Cisco-IOS-XE-cellwan-oper (cellwan-gps, cellwan-radio)
- Cisco-IOS-XE-gnss-dr-oper (GNSS/GPS/DR module)
- Cisco-IOS-XE-gnss-oper (dedicated GNSS module, when present)

Troubleshooting on the router:
- show cellular <slot> gps
- show netconf-yang statistics
========================================
"""
