#!/usr/bin/env python3
"""
Example usage of the Cisco GPS NETCONF tool

This script demonstrates how to use the cisco-gps-netconf package
to retrieve GPS coordinates from a Cisco router.
"""

from cisco_gps_netconf import CiscoGPSRetriever
from cisco_gps_netconf.exceptions import CiscoGPSError

def main():
    """Main example function"""
    
    # Router connection details
    router_config = {
        "host": "192.168.1.1",      # Replace with your router's IP
        "port": 830,                # NETCONF port
        "username": "admin",        # Replace with your username
        "password": "password",     # Replace with your password
        "timeout": 30               # Connection timeout in seconds
    }
    
    print("Cisco GPS NETCONF Retrieval Example")
    print("=" * 40)
    
    try:
        # Create GPS retriever instance
        gps_retriever = CiscoGPSRetriever(**router_config)
        
        # Retrieve and display GPS coordinates
        print(f"Connecting to router at {router_config['host']}...")
        gps_data = gps_retriever.retrieve_and_display_gps(
            output_file="example_gps_data.json"
        )
        
        # Additional processing of GPS data
        if gps_data:
            print("\n" + "=" * 40)
            print("SUCCESS: GPS coordinates retrieved!")
            print(f"Latitude: {gps_data.get('latitude', 'N/A')}")
            print(f"Longitude: {gps_data.get('longitude', 'N/A')}")
            if 'altitude' in gps_data:
                print(f"Altitude: {gps_data['altitude']}")
            if 'accuracy' in gps_data:
                print(f"Accuracy: {gps_data['accuracy']}")
        
    except CiscoGPSError as e:
        print(f"\nGPS Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check if NETCONF is enabled on the router")
        print("2. Verify GPS is configured: 'show gps status'")
        print("3. Check network connectivity to the router")
        
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("Please check your router configuration and network connectivity.")

if __name__ == "__main__":
    main()
