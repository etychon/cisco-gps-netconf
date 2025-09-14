"""
Tests for GPS retriever functionality
"""

import pytest
from unittest.mock import Mock, patch
from cisco_gps_netconf.gps_retriever import CiscoGPSRetriever
from cisco_gps_netconf.exceptions import ConnectionError, AuthenticationError


class TestCiscoGPSRetriever:
    """Test cases for CiscoGPSRetriever"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.retriever = CiscoGPSRetriever(
            host="192.168.1.1",
            username="test_user",
            password="test_pass"
        )
    
    def test_init(self):
        """Test initialization"""
        assert self.retriever.connection_params["host"] == "192.168.1.1"
        assert self.retriever.connection_params["port"] == 830
        assert self.retriever.connection_params["username"] == "test_user"
    
    @patch('cisco_gps_netconf.gps_retriever.manager')
    def test_connect_success(self, mock_manager):
        """Test successful connection"""
        mock_connection = Mock()
        mock_manager.connect.return_value = mock_connection
        
        connection = self.retriever.connect()
        
        assert connection == mock_connection
        mock_manager.connect.assert_called_once()
    
    @patch('cisco_gps_netconf.gps_retriever.manager')
    def test_connect_auth_failure(self, mock_manager):
        """Test authentication failure"""
        mock_manager.connect.side_effect = Exception("authentication failed")
        
        with pytest.raises(AuthenticationError):
            self.retriever.connect()
    
    @patch('cisco_gps_netconf.gps_retriever.manager')
    def test_connect_connection_failure(self, mock_manager):
        """Test connection failure"""
        mock_manager.connect.side_effect = Exception("connection refused")
        
        with pytest.raises(ConnectionError):
            self.retriever.connect()
    
    def test_extract_coordinates_from_xml(self):
        """Test coordinate extraction from XML"""
        import xml.etree.ElementTree as ET
        
        xml_data = """
        <root>
            <gps>
                <latitude>37.7749</latitude>
                <longitude>-122.4194</longitude>
                <altitude>52.0</altitude>
            </gps>
        </root>
        """
        
        root = ET.fromstring(xml_data)
        result = self.retriever._extract_coordinates_from_xml(root)
        
        assert result is not None
        assert result['latitude'] == '37.7749'
        assert result['longitude'] == '-122.4194'
        assert result['altitude'] == '52.0'
    
    def test_extract_coordinates_insufficient_data(self):
        """Test extraction with insufficient coordinate data"""
        import xml.etree.ElementTree as ET
        
        xml_data = """
        <root>
            <gps>
                <latitude>37.7749</latitude>
            </gps>
        </root>
        """
        
        root = ET.fromstring(xml_data)
        result = self.retriever._extract_coordinates_from_xml(root)
        
        assert result is None
