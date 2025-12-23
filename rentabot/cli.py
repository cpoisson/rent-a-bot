"""
rentabot.cli
~~~~~~~~~~~~

This module contains the Rent-A-Bot CLI application.
"""

import argparse
import os
from pathlib import Path

from rentabot import __version__


def find_config_file():
    """
    Discover configuration file using the following priority:
    1. Current directory: ./.rentabot.yaml or ./rentabot.yaml
    2. Home directory: ~/.rentabot/config.yaml
    3. Environment variable: RENTABOT_RESOURCE_DESCRIPTOR
    4. None (start with empty resources)

    Returns:
        str or None: Path to config file if found, None otherwise
    """
    # Check current directory
    for filename in [".rentabot.yaml", "rentabot.yaml"]:
        config_path = Path.cwd() / filename
        if config_path.exists():
            return str(config_path)

    # Check home directory
    home_config = Path.home() / ".rentabot" / "config.yaml"
    if home_config.exists():
        return str(home_config)

    # Check environment variable
    env_config = os.environ.get("RENTABOT_RESOURCE_DESCRIPTOR")
    if env_config and Path(env_config).exists():
        return env_config

    return None


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Rent-A-Bot - Your automation resource provider",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        metavar="FILE",
        help="Path to resource descriptor YAML file",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="Port to bind (default: 8000)",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["critical", "error", "warning", "info", "debug"],
        default="info",
        help="Log level (default: info)",
    )

    args = parser.parse_args()

    # Determine config file
    config_file = args.config or find_config_file()

    # Set environment variable for the FastAPI app to use
    if config_file:
        os.environ["RENTABOT_RESOURCE_DESCRIPTOR"] = config_file
        print(f"Using config file: {config_file}")
    else:
        print("No config file found, starting with empty resources")

    # Print startup info
    print(f"Starting Rent-A-Bot v{__version__}")
    print(f"Server: http://{args.host}:{args.port}")
    print(f"API Docs: http://{args.host}:{args.port}/docs")

    # Import and run uvicorn
    import uvicorn

    uvicorn.run(
        "rentabot.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
