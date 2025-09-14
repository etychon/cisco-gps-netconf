"""
Custom exceptions for Cisco GPS NETCONF operations
"""


class CiscoGPSError(Exception):
    """Base exception for Cisco GPS operations"""
    pass


class ConnectionError(CiscoGPSError):
    """Raised when connection to router fails"""
    pass


class AuthenticationError(CiscoGPSError):
    """Raised when authentication fails"""
    pass


class GPSNotFoundError(CiscoGPSError):
    """Raised when GPS data is not found on the router"""
    pass


class InvalidCoordinatesError(CiscoGPSError):
    """Raised when GPS coordinates are invalid or malformed"""
    pass
