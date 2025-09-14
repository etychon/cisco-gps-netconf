"""
Coordinate formatting utilities
"""

from typing import Dict, Any, List


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
