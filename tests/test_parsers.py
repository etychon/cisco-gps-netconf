"""
Tests for NETCONF GPS XML parsers
"""

import pytest
import xml.etree.ElementTree as ET

from cisco_gps_netconf.parsers import (
    parse_cellwan_gps,
    parse_gnss_dr_data,
    parse_gps_sources_from_xml,
    parse_coordinate_value,
    parse_radio_from_xml,
)


CELLWAN_GPS_XML = """
<cellwan-gps>
  <cellular-interface>Cellular0/4/0</cellular-interface>
  <gps-feature-state>gps-enabled</gps-feature-state>
  <state>gps-state-acquiring</state>
  <latitude>50 Deg 36 Min 0.5472 Sec North</latitude>
  <longitude>5 Deg 37 Min 17.9300 Sec East</longitude>
  <timestamp>2026-07-01T08:39:36+00:00</timestamp>
</cellwan-gps>
"""

CELLWAN_GPS_5_XML = """
<cellwan-gps>
  <cellular-interface>Cellular0/5/0</cellular-interface>
  <state>gps-state-enabled</state>
  <latitude>50 Deg 36 Min 45.0171 Sec North</latitude>
  <longitude>5 Deg 35 Min 12.1052 Sec East</longitude>
  <timestamp>2026-07-01T08:39:12+00:00</timestamp>
</cellwan-gps>
"""

GNSS_DR_XML = """
<gnss-dr-data>
  <feature-state>gps-dr-feature-enabled</feature-state>
  <oper-state>gps-dr-state-enabled</oper-state>
  <latitude>50.612567</latitude>
  <longitude>5.586677</longitude>
  <timestamp>2026-07-01T08:39:38+00:00</timestamp>
</gnss-dr-data>
"""

CELLWAN_RADIO_XML = """
<cellwan-radio>
  <cellular-interface>Cellular0/5/0</cellular-interface>
  <radio-power-mode>radio-power-mode-online</radio-power-mode>
  <radio-rssi>-74</radio-rssi>
  <radio-rsrp>-103</radio-rsrp>
  <radio-band>7</radio-band>
</cellwan-radio>
"""


class TestCoordinateParsing:
    def test_dms_latitude(self):
        result = parse_coordinate_value("50 Deg 36 Min 45.0171 Sec North", "latitude")
        assert "latitude" in result
        assert float(result["latitude"]) == pytest.approx(50.61250475, rel=1e-4)
        assert "latitude_dms" in result

    def test_decimal_longitude(self):
        result = parse_coordinate_value("5.586677", "longitude")
        assert result["longitude"] == "5.586677"


class TestCellwanGpsParser:
    def test_parse_cellular_4_0(self):
        elem = ET.fromstring(CELLWAN_GPS_XML)
        result = parse_cellwan_gps(elem)
        assert result is not None
        assert result["source"] == "Cellular0/4/0"
        assert result["source_type"] == "cellular"
        assert float(result["latitude"]) > 50.6
        assert float(result["longitude"]) > 5.6

    def test_parse_cellular_5_0(self):
        elem = ET.fromstring(CELLWAN_GPS_5_XML)
        result = parse_cellwan_gps(elem)
        assert result is not None
        assert result["source"] == "Cellular0/5/0"


class TestGnssDrParser:
    def test_parse_gnss_dr(self):
        elem = ET.fromstring(GNSS_DR_XML)
        result = parse_gnss_dr_data(elem)
        assert result is not None
        assert result["source"] == "GNSS_GPS_DR"
        assert result["latitude"] == "50.612567"
        assert result["longitude"] == "5.586677"


class TestMultiSourceAssembly:
    def test_all_sources_from_response(self):
        xml = f"<root>{CELLWAN_GPS_XML}{CELLWAN_GPS_5_XML}{GNSS_DR_XML}</root>"
        sources = parse_gps_sources_from_xml(xml)
        assert "Cellular0/4/0" in sources
        assert "Cellular0/5/0" in sources
        assert "GNSS_GPS_DR" in sources

    def test_empty_response(self):
        assert parse_gps_sources_from_xml("<rpc-reply><data/></rpc-reply>") == {}

    def test_radio_parser(self):
        xml = f"<root>{CELLWAN_RADIO_XML}</root>"
        radios = parse_radio_from_xml(xml)
        assert "Cellular0/5/0" in radios
        assert radios["Cellular0/5/0"]["radio_rssi"] == "-74"
