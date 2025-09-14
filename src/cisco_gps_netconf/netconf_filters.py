"""
NETCONF filter definitions for different Cisco router models and YANG schemas
"""


class NetconfFilters:
    """Collection of NETCONF filters for GPS data retrieval"""
    
    def get_iosxe_native_filter(self) -> str:
        """Get IOS XE native YANG model GPS filter"""
        return """
        <filter>
            <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
                <gps>
                    <location/>
                </gps>
            </native>
        </filter>
        """
    
    def get_iosxe_gps_filter(self) -> str:
        """Get IOS XE GPS-specific YANG model filter"""
        return """
        <filter>
            <gps xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-gps">
                <location/>
                <coordinates/>
            </gps>
        </filter>
        """
    
    def get_generic_location_filter(self) -> str:
        """Get generic location filter"""
        return """
        <filter>
            <location xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-location">
                <gps/>
                <coordinates/>
            </location>
        </filter>
        """
    
    def get_broad_gps_filter(self) -> str:
        """Get broad GPS filter without namespace restrictions"""
        return """
        <filter>
            <gps/>
        </filter>
        """
    
    def get_ios_xr_filter(self) -> str:
        """Get IOS XR GPS filter"""
        return """
        <filter>
            <gnss xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-gnss-oper">
                <gnss-receiver-info/>
            </gnss>
        </filter>
        """
    
    def get_nexus_filter(self) -> str:
        """Get Nexus GPS filter"""
        return """
        <filter>
            <System xmlns="http://cisco.com/ns/yang/cisco-nx-os-device">
                <gps-items/>
            </System>
        </filter>
        """
