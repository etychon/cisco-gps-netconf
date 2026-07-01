"""
Tests for GPS retriever functionality
"""

import pytest
from unittest.mock import Mock, patch

from cisco_gps_netconf.gps_retriever import CiscoGPSRetriever
from cisco_gps_netconf.exceptions import ConnectionError, AuthenticationError


class TestCiscoGPSRetriever:
    def setup_method(self):
        self.retriever = CiscoGPSRetriever(
            host="192.168.1.1",
            username="test_user",
            password="test_pass",
        )

    def test_init(self):
        assert self.retriever.connection_params["host"] == "192.168.1.1"
        assert self.retriever.connection_params["port"] == 830

    @patch("cisco_gps_netconf.gps_retriever.manager")
    def test_connect_success(self, mock_manager):
        mock_connection = Mock()
        mock_manager.connect.return_value = mock_connection
        connection = self.retriever.connect()
        assert connection == mock_connection

    @patch("cisco_gps_netconf.gps_retriever.manager")
    def test_connect_auth_failure(self, mock_manager):
        mock_manager.connect.side_effect = Exception("authentication failed")
        with pytest.raises(AuthenticationError):
            self.retriever.connect()

    @patch("cisco_gps_netconf.gps_retriever.manager")
    def test_connect_connection_failure(self, mock_manager):
        mock_manager.connect.side_effect = Exception("connection refused")
        with pytest.raises(ConnectionError):
            self.retriever.connect()

    @patch.object(CiscoGPSRetriever, "_netconf_get")
    def test_get_all_gps_sources_skips_failures(self, mock_get):
        gnss_dr_xml = """
        <data><gnss-dr-data>
          <latitude>50.1</latitude><longitude>5.1</longitude>
        </gnss-dr-data></data>
        """
        mock_get.side_effect = [gnss_dr_xml, None, None]
        connection = Mock()
        sources = self.retriever.get_all_gps_sources(connection)
        assert "GNSS_GPS_DR" in sources
        assert sources["GNSS_GPS_DR"]["latitude"] == "50.1"
