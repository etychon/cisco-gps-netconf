"""
Command line interface for the Cisco GPS NETCONF tool
"""

import argparse
import sys
from .gps_retriever import CiscoGPSRetriever
from .exceptions import CiscoGPSError


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="Retrieve GPS coordinates from Cisco router via NETCONF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    cisco-gps-netconf -H 192.168.1.1 -u admin -p password
    cisco-gps-netconf -H router.example.com -u netconf_user -p secret123 -P 2022
    cisco-gps-netconf -H 10.1.1.1 -u admin -p pass -o gps_data.json --timeout 60
        """
    )
    
    # Required arguments
    parser.add_argument('-H', '--host', required=True, 
                       help='Router IP address or hostname')
    parser.add_argument('-u', '--username', required=True,
                       help='Router username')
    parser.add_argument('-p', '--password', required=True,
                       help='Router password')
    
    # Optional arguments
    parser.add_argument('-P', '--port', type=int, default=830,
                       help='NETCONF port (default: 830)')
    parser.add_argument('-o', '--output', 
                       help='Output file to save GPS data (JSON format)')
    parser.add_argument('-t', '--timeout', type=int, default=30,
                       help='Connection timeout in seconds (default: 30)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    
    return parser


def main():
    """Main CLI function"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Create GPS retriever instance
    try:
        gps_retriever = CiscoGPSRetriever(
            host=args.host,
            port=args.port,
            username=args.username,
            password=args.password,
            timeout=args.timeout
        )
        
        # Retrieve and display GPS coordinates
        gps_data = gps_retriever.retrieve_and_display_gps(output_file=args.output)
        
        if args.verbose:
            print(f"\nRaw GPS data: {gps_data}")
        
        sys.exit(0)
        
    except CiscoGPSError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
