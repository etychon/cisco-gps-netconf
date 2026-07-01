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
        "host": "192.168.2.191",
        "port": 830,
        "username": "netconf_user",
        "password": "<password>",
        "timeout": 30,
        "interfaces": ["Cellular0/4/0", "Cellular0/5/0"],
    }
    
    print("Cisco GPS NETCONF Retrieval Example")
    print("=" * 40)
    
    try:
        # Create GPS retriever instance
        gps_retriever = CiscoGPSRetriever(**router_config)
        
        # Retrieve and display GPS coordinates
        print(f"Connecting to router at {router_config['host']}...")
        sources = gps_retriever.retrieve_and_display_gps(
            output_file="example_gps_data.json"
        )

        if sources:
            print("\n" + "=" * 40)
            print(f"SUCCESS: {len(sources)} GPS source(s) retrieved!")
            for source_id, gps_data in sources.items():
                print(f"  {source_id}: {gps_data.get('latitude')}, {gps_data.get('longitude')}")
        
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
