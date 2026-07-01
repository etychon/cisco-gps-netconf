"""
Coordinate formatting utilities
"""

from typing import Dict, Any, List


class CoordinateFormatter:
    """Handles formatting of GPS coordinates in various formats."""

    def format_all_sources(self, sources: Dict[str, Dict[str, Any]]) -> str:
        """Format multiple GPS sources for display."""
        if not sources:
            return "No GPS coordinates found"

        output: List[str] = []
        output.append("=" * 60)
        output.append("GPS COORDINATES RETRIEVED")
        output.append(f"Sources: {len(sources)}")
        output.append("=" * 60)

        for source_id, gps_data in sources.items():
            output.append("")
            output.append(f"Source: {source_id}")
            output.append("-" * 40)
            output.extend(self._format_single_source_lines(gps_data))

        output.append("=" * 60)
        return "\n".join(output)

    def format_coordinates(self, gps_data: Dict[str, Any]) -> str:
        """Format a single GPS source (backward compatible)."""
        if not gps_data:
            return "No GPS coordinates found"

        output: List[str] = []
        output.append("=" * 60)
        output.append("GPS COORDINATES RETRIEVED")
        output.append("=" * 60)
        output.extend(self._format_single_source_lines(gps_data))
        output.append("=" * 60)
        return "\n".join(output)

    def format_cellular_report(
        self,
        sources: Dict[str, Dict[str, Any]],
        radios: Dict[str, Dict[str, Any]],
    ) -> str:
        """Format GPS sources and optional per-interface radio metrics."""
        output: List[str] = []
        output.append("=" * 60)
        output.append("CELLULAR DATA RETRIEVED")
        output.append("=" * 60)

        if sources:
            output.append(f"\nGPS SOURCES ({len(sources)}):")
            output.append("-" * 20)
            for source_id, gps_data in sources.items():
                output.append(f"\n[{source_id}]")
                output.extend(self._format_single_source_lines(gps_data, indent="  "))

        if radios:
            output.append(f"\n\nCELLULAR RADIO INFORMATION ({len(radios)} interfaces):")
            output.append("-" * 30)
            for iface, radio_data in radios.items():
                output.append(f"\nInterface: {iface}")
                self._append_radio_lines(output, radio_data, indent="  ")

        output.append("=" * 60)
        return "\n".join(output)

    def _format_single_source_lines(
        self, gps_data: Dict[str, Any], indent: str = ""
    ) -> List[str]:
        lines: List[str] = []

        if gps_data.get("source_type"):
            lines.append(f"{indent}Type: {gps_data['source_type']}")
        if gps_data.get("yang_model"):
            lines.append(f"{indent}YANG: {gps_data['yang_model']}")
        if gps_data.get("cli_equivalent"):
            lines.append(f"{indent}CLI equivalent: {gps_data['cli_equivalent']}")

        if "latitude" in gps_data and "longitude" in gps_data:
            lat = gps_data["latitude"]
            lon = gps_data["longitude"]
            lines.append(f"{indent}Decimal Degrees:")
            lines.append(f"{indent}  Latitude:  {lat}°")
            lines.append(f"{indent}  Longitude: {lon}°")

            if "latitude_dms" in gps_data and "longitude_dms" in gps_data:
                lines.append(f"{indent}Degrees, Minutes, Seconds:")
                lines.append(f"{indent}  Latitude:  {gps_data['latitude_dms']}")
                lines.append(f"{indent}  Longitude: {gps_data['longitude_dms']}")
            else:
                try:
                    lat_float = float(lat)
                    lon_float = float(lon)
                    lines.append(f"{indent}Degrees, Minutes, Seconds:")
                    lines.append(
                        f"{indent}  Latitude:  {self._decimal_to_dms(lat_float, 'latitude')}"
                    )
                    lines.append(
                        f"{indent}  Longitude:  {self._decimal_to_dms(lon_float, 'longitude')}"
                    )
                except ValueError:
                    pass

            try:
                lat_float = float(lat)
                lon_float = float(lon)
                lines.extend(
                    self._generate_map_links(lat_float, lon_float, indent=indent)
                )
            except ValueError:
                pass

        self._add_additional_info(lines, gps_data, indent=indent)
        return lines

    def _append_radio_lines(
        self, output: List[str], radio_data: Dict[str, Any], indent: str = ""
    ) -> None:
        field_labels = {
            "radio_power_mode": "Power Mode",
            "radio_lte_band": "LTE Band",
            "radio_lte_bandwidth": "LTE Bandwidth",
            "radio_lte_rx_channel": "LTE Rx Channel (PCC)",
            "radio_lte_tx_channel": "LTE Tx Channel (PCC)",
            "radio_rssi": "RSSI",
            "radio_rsrp": "RSRP",
            "radio_rsrq": "RSRQ",
            "radio_snr": "SNR",
            "radio_physical_cell_id": "Physical Cell ID",
            "radio_rat_preference": "RAT Preference",
            "radio_rat_selected": "RAT Selected",
            "radio_technology": "Technology",
        }
        for key, label in field_labels.items():
            if key in radio_data:
                value = radio_data[key]
                unit = ""
                if key in ("radio_rssi", "radio_rsrp"):
                    unit = " dBm"
                elif key in ("radio_rsrq",):
                    unit = " dB"
                elif key == "radio_snr":
                    unit = " dB"
                output.append(f"{indent}{label}: {value}{unit}")

    def _decimal_to_dms(self, decimal_degrees: float, coord_type: str) -> str:
        is_negative = decimal_degrees < 0
        decimal_degrees = abs(decimal_degrees)

        degrees = int(decimal_degrees)
        minutes_float = (decimal_degrees - degrees) * 60
        minutes = int(minutes_float)
        seconds = (minutes_float - minutes) * 60

        if coord_type == "latitude":
            direction = "S" if is_negative else "N"
        else:
            direction = "W" if is_negative else "E"

        return f"{degrees}° {minutes}' {seconds:.2f}\" {direction}"

    def _generate_map_links(
        self, lat: float, lon: float, indent: str = ""
    ) -> List[str]:
        return [
            f"{indent}Map Links:",
            f"{indent}  Google Maps: https://www.google.com/maps?q={lat},{lon}",
            f"{indent}  OpenStreetMap: https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=15",
            f"{indent}  Bing Maps: https://www.bing.com/maps?cp={lat}~{lon}&lvl=15",
        ]

    def _add_additional_info(
        self, output: List[str], gps_data: Dict[str, Any], indent: str = ""
    ) -> None:
        if "altitude" in gps_data:
            output.append(f"{indent}Altitude: {gps_data['altitude']}")
        if "accuracy" in gps_data:
            output.append(f"{indent}Accuracy: {gps_data['accuracy']}")
        if "timestamp" in gps_data:
            output.append(f"{indent}Timestamp: {gps_data['timestamp']}")
        if "gps_status" in gps_data:
            output.append(f"{indent}GPS Status: {gps_data['gps_status']}")
        if "gps_mode" in gps_data:
            output.append(f"{indent}GPS Mode: {gps_data['gps_mode']}")

        excluded = {
            "latitude",
            "longitude",
            "latitude_dms",
            "longitude_dms",
            "altitude",
            "accuracy",
            "timestamp",
            "gps_status",
            "gps_mode",
            "source",
            "source_type",
            "yang_model",
            "cli_equivalent",
        }
        other_data = {k: v for k, v in gps_data.items() if k not in excluded}
        if other_data:
            output.append(f"{indent}Additional Data:")
            for key, value in other_data.items():
                output.append(f"{indent}  {key.replace('_', ' ').title()}: {value}")
