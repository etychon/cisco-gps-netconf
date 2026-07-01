"""
Command line interface for the Cisco GPS NETCONF tool
"""

import argparse
import sys
from typing import List, Optional

from .gps_retriever import CiscoGPSRetriever
from .exceptions import CiscoGPSError


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Retrieve GPS coordinates from Cisco routers via NETCONF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    cisco-gps-netconf -H 192.168.2.191 -u cisco -p cisco
    cisco-gps-netconf -H 192.168.2.191 -u cisco -p cisco --cellular -o gps.json
    cisco-gps-netconf -H 192.168.2.191 -u cisco -p cisco \\
        --interfaces Cellular0/4/0,Cellular0/5/0
        """,
    )

    parser.add_argument("-H", "--host", required=True, help="Router IP address or hostname")
    parser.add_argument("-u", "--username", required=True, help="Router username")
    parser.add_argument("-p", "--password", required=True, help="Router password")
    parser.add_argument("-P", "--port", type=int, default=830, help="NETCONF port (default: 830)")
    parser.add_argument("-o", "--output", help="Output file (JSON)")
    parser.add_argument("-t", "--timeout", type=int, default=30, help="Connection timeout in seconds")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print raw JSON result")
    parser.add_argument(
        "--cellular",
        action="store_true",
        help="Include per-interface cellular radio metrics",
    )
    parser.add_argument(
        "--interfaces",
        help="Comma-separated cellular interfaces to include (default: all discovered)",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 2.0.0")

    return parser


def _parse_interfaces(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    return [part.strip() for part in value.split(",") if part.strip()]


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        retriever = CiscoGPSRetriever(
            host=args.host,
            port=args.port,
            username=args.username,
            password=args.password,
            timeout=args.timeout,
            interfaces=_parse_interfaces(args.interfaces),
        )

        if args.cellular:
            result = retriever.retrieve_and_display_cellular(output_file=args.output)
        else:
            result = retriever.retrieve_and_display_gps(output_file=args.output)

        if args.verbose:
            print(f"\nRaw data: {result}")

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
