"""
XML and coordinate parsing for Cisco NETCONF GPS responses.
"""

import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional, List

DMS_COORD_PATTERN = re.compile(
    r"(\d+)\s+Deg\s+(\d+)\s+Min\s+([\d.]+)\s+Sec\s+(North|South|East|West)",
    re.IGNORECASE,
)

DECIMAL_COORD_PATTERN = re.compile(r"^-?\d+(\.\d+)?$")


def _local_name(tag: str) -> str:
    if not tag:
        return ""
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def dms_to_decimal(degrees: int, minutes: int, seconds: float, direction: str) -> float:
    """Convert DMS components to signed decimal degrees."""
    decimal = degrees + minutes / 60 + seconds / 3600
    direction = direction.upper()
    if direction in ("SOUTH", "WEST", "S", "W"):
        decimal = -decimal
    return decimal


def parse_coordinate_value(value: str, coord_type: str) -> Dict[str, str]:
    """
    Parse a latitude or longitude string (decimal or DMS) into normalized fields.

    Returns dict with decimal string and optional *_dms key.
    """
    value = value.strip()
    result: Dict[str, str] = {}

    if DECIMAL_COORD_PATTERN.match(value):
        result[coord_type] = value
        return result

    match = DMS_COORD_PATTERN.search(value)
    if not match:
        result[coord_type] = value
        return result

    degrees = int(match.group(1))
    minutes = int(match.group(2))
    seconds = float(match.group(3))
    direction = match.group(4)
    decimal = dms_to_decimal(degrees, minutes, seconds, direction)
    result[coord_type] = str(decimal)
    result[f"{coord_type}_dms"] = (
        f"{degrees}° {minutes}' {seconds}\" {direction[0].upper()}"
    )
    return result


def _child_text(elem: ET.Element, name: str) -> Optional[str]:
    for child in elem:
        if _local_name(child.tag) == name and child.text:
            text = child.text.strip()
            if text:
                return text
    return None


def parse_gnss_dr_data(elem: ET.Element) -> Optional[Dict[str, Any]]:
    """Parse gnss-dr-data element into a GPS source dict."""
    lat = _child_text(elem, "latitude")
    lon = _child_text(elem, "longitude")
    if not lat or not lon:
        return None

    data: Dict[str, Any] = {
        "source": "GNSS_GPS_DR",
        "source_type": "platform_hardware_gps",
        "yang_model": "Cisco-IOS-XE-gnss-dr-oper",
        "cli_equivalent": "show platform hardware gps detail",
    }
    data.update(parse_coordinate_value(lat, "latitude"))
    data.update(parse_coordinate_value(lon, "longitude"))

    for field, tag in (
        ("timestamp", "timestamp"),
        ("feature_state", "feature-state"),
        ("oper_state", "oper-state"),
        ("dr_loc_used", "dr-loc-used"),
        ("gps_status", "oper-state"),
        ("gps_mode_used", "dr-loc-used"),
    ):
        val = _child_text(elem, tag)
        if val:
            data[field] = val

    return data


def parse_cellwan_gps(elem: ET.Element) -> Optional[Dict[str, Any]]:
    """Parse cellwan-gps element into a GPS source dict."""
    interface = _child_text(elem, "cellular-interface")
    lat = _child_text(elem, "latitude")
    lon = _child_text(elem, "longitude")
    if not interface or not lat or not lon:
        return None

    data: Dict[str, Any] = {
        "source": interface,
        "source_type": "cellular",
        "yang_model": "Cisco-IOS-XE-cellwan-oper",
    }
    data.update(parse_coordinate_value(lat, "latitude"))
    data.update(parse_coordinate_value(lon, "longitude"))

    for field, tag in (
        ("timestamp", "timestamp"),
        ("gps_status", "state"),
        ("gps_feature_state", "gps-feature-state"),
        ("gps_mode", "mode-selected"),
        ("gps_port", "port-selected"),
    ):
        val = _child_text(elem, tag)
        if val:
            data[field] = val

    return data


def parse_gnss_oper_data(elem: ET.Element) -> Optional[Dict[str, Any]]:
    """Parse gnss-data element when location container is present."""
    slot = _child_text(elem, "slot")
    location = None
    for child in elem:
        if _local_name(child.tag) == "location":
            location = child
            break

    if location is None:
        return None

    lat = _child_text(location, "latitude")
    lon = _child_text(location, "longitude")
    if not lat or not lon:
        return None

    source_id = f"gnss_oper_slot_{slot}" if slot else "gnss_oper"
    data: Dict[str, Any] = {
        "source": source_id,
        "source_type": "gnss_module",
        "yang_model": "Cisco-IOS-XE-gnss-oper",
    }
    if slot:
        data["slot"] = slot
    data.update(parse_coordinate_value(lat, "latitude"))
    data.update(parse_coordinate_value(lon, "longitude"))

    height = _child_text(location, "height")
    if height:
        data["altitude"] = height

    ts = _child_text(elem, "timestamp")
    if ts:
        data["timestamp"] = ts

    lock = _child_text(elem, "lock-status")
    if lock:
        data["gps_status"] = lock

    return data


def parse_cellwan_radio(elem: ET.Element) -> Dict[str, Any]:
    """Parse cellwan-radio element into radio metrics dict."""
    interface = _child_text(elem, "cellular-interface") or "unknown"
    radio: Dict[str, Any] = {"cellular_interface": interface}

    mapping = {
        "power_mode": "radio-power-mode",
        "lte_rx_channel": "radio-rx-channel",
        "lte_tx_channel": "radio-tx-channel",
        "lte_band": "radio-band",
        "lte_bandwidth": "bandwidth",
        "rssi": "radio-rssi",
        "rsrp": "radio-rsrp",
        "rsrq": "radio-rsrq",
        "snr": "radio-snr",
        "physical_cell_id": "pci",
        "rat_preference": "radio-rat-preference",
        "rat_selected": "radio-rat-selected",
        "technology": "technology",
    }
    for key, tag in mapping.items():
        val = _child_text(elem, tag)
        if val:
            radio[f"radio_{key}"] = val

    return radio


def parse_gps_sources_from_xml(xml_response: str) -> Dict[str, Dict[str, Any]]:
    """Extract all GPS sources from a NETCONF XML response."""
    sources: Dict[str, Dict[str, Any]] = {}
    try:
        root = ET.fromstring(xml_response)
    except ET.ParseError:
        return sources

    for elem in root.iter():
        name = _local_name(elem.tag)
        if name == "gnss-dr-data":
            parsed = parse_gnss_dr_data(elem)
            if parsed:
                sources[parsed["source"]] = parsed
        elif name == "cellwan-gps":
            parsed = parse_cellwan_gps(elem)
            if parsed:
                sources[parsed["source"]] = parsed
        elif name == "gnss-data":
            parsed = parse_gnss_oper_data(elem)
            if parsed:
                sources[parsed["source"]] = parsed

    return sources


def parse_radio_from_xml(xml_response: str) -> Dict[str, Dict[str, Any]]:
    """Extract per-interface radio data from cellwan-radio XML."""
    radios: Dict[str, Dict[str, Any]] = {}
    try:
        root = ET.fromstring(xml_response)
    except ET.ParseError:
        return radios

    for elem in root.iter():
        if _local_name(elem.tag) != "cellwan-radio":
            continue
        parsed = parse_cellwan_radio(elem)
        iface = parsed.get("cellular_interface", "unknown")
        radios[iface] = parsed

    return radios
