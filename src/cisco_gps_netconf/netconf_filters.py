"""
NETCONF filter definitions for Cisco IOS XE GPS operational YANG models.
"""

from typing import Tuple, Optional, List

FilterTuple = Tuple[str, str]

CELLWAN_OPER_NS = "http://cisco.com/ns/yang/Cisco-IOS-XE-cellwan-oper"
GNSS_DR_OPER_NS = "http://cisco.com/ns/yang/Cisco-IOS-XE-gnss-dr-oper"
GNSS_OPER_NS = "http://cisco.com/ns/yang/Cisco-IOS-XE-gnss-oper"


class NetconfFilters:
    """Collection of NETCONF subtree filters for GPS data retrieval."""

    def get_cellwan_gps_filter(self, interface: Optional[str] = None) -> FilterTuple:
        """Operational cellular GPS from Cisco-IOS-XE-cellwan-oper."""
        if interface:
            inner = (
                f'<cellwan-oper-data xmlns="{CELLWAN_OPER_NS}">'
                f"<cellwan-gps><cellular-interface>{interface}</cellular-interface></cellwan-gps>"
                f"</cellwan-oper-data>"
            )
        else:
            inner = (
                f'<cellwan-oper-data xmlns="{CELLWAN_OPER_NS}">'
                f"<cellwan-gps/>"
                f"</cellwan-oper-data>"
            )
        return ("subtree", inner)

    def get_cellwan_radio_filter(self, interface: Optional[str] = None) -> FilterTuple:
        """Operational cellular radio from Cisco-IOS-XE-cellwan-oper."""
        if interface:
            inner = (
                f'<cellwan-oper-data xmlns="{CELLWAN_OPER_NS}">'
                f"<cellwan-radio><cellular-interface>{interface}</cellular-interface></cellwan-radio>"
                f"</cellwan-oper-data>"
            )
        else:
            inner = (
                f'<cellwan-oper-data xmlns="{CELLWAN_OPER_NS}">'
                f"<cellwan-radio/>"
                f"</cellwan-oper-data>"
            )
        return ("subtree", inner)

    def get_gnss_dr_oper_filter(self) -> FilterTuple:
        """GNSS/GPS/DR module coordinates from Cisco-IOS-XE-gnss-dr-oper."""
        return (
            "subtree",
            f'<gnss-dr-oper-data xmlns="{GNSS_DR_OPER_NS}"/>',
        )

    def get_gnss_oper_filter(self) -> FilterTuple:
        """Dedicated GNSS module from Cisco-IOS-XE-gnss-oper."""
        return (
            "subtree",
            f'<gnss-oper-data xmlns="{GNSS_OPER_NS}"/>',
        )

    def get_ios_xr_filter(self) -> FilterTuple:
        """IOS XR GNSS operational filter."""
        return (
            "subtree",
            '<gnss xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-gnss-oper">'
            "<gnss-receiver-info/>"
            "</gnss>",
        )

    def get_nexus_filter(self) -> FilterTuple:
        """Nexus GPS filter."""
        return (
            "subtree",
            '<System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">'
            "<gps-items/>"
            "</System>",
        )
