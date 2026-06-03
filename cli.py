"""Command-line interface for domain directory.

Provides argparse-based CLI with logging configuration and command dispatch.
"""

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
import os

from client import cmd_count, cmd_list, cmd_record, cmd_search, set_server_config
from serveur import start_server

# Load environment variables
load_dotenv()

DEFAULT_HOST = os.getenv("HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("PORT", "8888"))


def configure_logging(verbosity: int) -> None:
    """Configure logging based on verbosity level.

    Args:
        verbosity: Number of -v flags (0=WARNING, 1=INFO, 2=DEBUG, 3+=DEBUG with details)
    """
    if verbosity == 0:
        level = logging.WARNING
        format_str = "%(message)s"
    elif verbosity == 1:
        level = logging.INFO
        format_str = "%(message)s"
    elif verbosity == 2:
        level = logging.DEBUG
        format_str = "%(message)s"
    else:  # verbosity >= 3
        level = logging.DEBUG
        format_str = "%(asctime)s - %(name)s:%(lineno)d [%(threadName)s] - %(levelname)s - %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=level,
        format=format_str,
        stream=sys.stderr,
    )


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Domain directory - networked hostname repository"
    )

    # Global verbosity flag
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v, -vv, -vvv)",
    )

    # Subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start the server")
    serve_parser.add_argument(
        "--host", default=DEFAULT_HOST, help=f"Server host (default: {DEFAULT_HOST})"
    )
    serve_parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help=f"Server port (default: {DEFAULT_PORT})"
    )

    # search command
    search_parser = subparsers.add_parser("search", help="Search for a domain")
    search_parser.add_argument("hote", help="Hostname to search")
    search_parser.add_argument(
        "--host", default=DEFAULT_HOST, help=f"Server host (default: {DEFAULT_HOST})"
    )
    search_parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help=f"Server port (default: {DEFAULT_PORT})"
    )

    # record command
    record_parser = subparsers.add_parser("record", help="Record a new domain")
    record_parser.add_argument("hote", help="Hostname to record")
    record_parser.add_argument(
        "--host", default=DEFAULT_HOST, help=f"Server host (default: {DEFAULT_HOST})"
    )
    record_parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help=f"Server port (default: {DEFAULT_PORT})"
    )

    # count command
    count_parser = subparsers.add_parser("count", help="Count recorded domains")
    count_parser.add_argument(
        "--host", default=DEFAULT_HOST, help=f"Server host (default: {DEFAULT_HOST})"
    )
    count_parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help=f"Server port (default: {DEFAULT_PORT})"
    )

    # list command
    list_parser = subparsers.add_parser("list", help="List all domains")
    list_parser.add_argument(
        "--host", default=DEFAULT_HOST, help=f"Server host (default: {DEFAULT_HOST})"
    )
    list_parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help=f"Server port (default: {DEFAULT_PORT})"
    )

    # Parse arguments
    args = parser.parse_args()

    # Configure logging
    configure_logging(args.verbose)

    # Dispatch commands
    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "serve":
        start_server(args.host, args.port)

    elif args.command == "search":
        set_server_config(args.host, args.port)
        domaine = cmd_search(args.hote)
        if domaine:
            print(f"Hostname: {domaine.hote}")
            print(f"IP: {domaine.ip}")
            print(f"Contact: {domaine.contact}")
            print(f"Email: {domaine.email}")
        else:
            print(f"Domain '{args.hote}' not found or server error", file=sys.stderr)
            sys.exit(1)

    elif args.command == "record":
        set_server_config(args.host, args.port)
        status = cmd_record(args.hote)
        print(f"Status: {status}")
        if status != "OK":
            sys.exit(1)

    elif args.command == "count":
        set_server_config(args.host, args.port)
        count = cmd_count()
        print(f"Total domains: {count}")

    elif args.command == "list":
        set_server_config(args.host, args.port)
        hotes = cmd_list()
        if hotes:
            for hote in hotes:
                print(hote)
        else:
            print("No domains recorded", file=sys.stderr)


if __name__ == "__main__":
    main()
