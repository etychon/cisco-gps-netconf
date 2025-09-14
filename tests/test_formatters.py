"""
Tests for coordinate formatters
"""

import pytest
from cisco_gps_netconf.formatters import CoordinateFormatter


class TestCoordinateFormatter:
    """Test cases for CoordinateFormatter"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.formatter = CoordinateFormatter()
    
    def test_decimal_to_dms_positive_latitude(self):
        """Test DMS conversion for positive latitude"""
        result = self.formatter._decimal_to_dms(37.7749, 'latitude')
        assert "37° 46' 29.64\" N" == result
    
    def test_decimal_to_dms_negative_latitude(self):
        """Test DMS conversion for negative latitude"""
        result = self.formatter._decimal_to_dms(-37.7749, 'latitude')
        assert "37° 46' 29.64\" S" == result
    
    def test_decimal_to_dms_positive_longitude(self):
        """Test DMS conversion for positive longitude"""
        result = self.formatter._decimal_to_dms(122.4194, 'longitude')
        assert "122° 25' 9.84\" E" == result
    
    def test_decimal_to_dms_negative_longitude(self):
        """Test DMS conversion for negative longitude"""
        result = self.formatter._decimal_to_dms(-122.4194, 'longitude')
        assert "122° 25' 9.84\" W" == result
    
    def test_format_coordinates_complete_data(self):
        """Test formatting with complete GPS data"""
        gps_data = {
            'latitude': '37.7749',
            'longitude': '-122.4194',
            'altitude': '52.0',
            'accuracy': '3.5'
        }
        
        result = self.formatter.format_coordinates(gps_data)
        
        assert 'GPS COORDINATES RETRIEVED' in result
        assert '37.7749°' in result
        assert '-122.4194°' in result
        assert 'Altitude: 52.0' in result
        assert 'Accuracy: 3.5' in result
        assert 'google.com/maps' in result
    
    def test_format_coordinates_minimal_data(self):
        """Test formatting with minimal GPS data"""
        gps_data = {
            'latitude': '37.7749',
            'longitude': '-122.4194'
        }
        
        result = self.formatter.format_coordinates(gps_data)
        
        assert 'GPS COORDINATES RETRIEVED' in result
        assert '37.7749°' in result
        assert '-122.4194°' in result
    
    def test_format_coordinates_empty_data(self):
        """Test formatting with empty data"""
        result = self.formatter.format_coordinates({})
        assert 'No GPS coordinates found' == result
    
    def test_format_coordinates_invalid_numeric(self):
        """Test formatting with non-numeric coordinates"""
        gps_data = {
            'latitude': 'invalid',
            'longitude': 'invalid'
        }
        
        result = self.formatter.format_coordinates(gps_data)
        
        assert 'Could not convert to DMS format' in result
